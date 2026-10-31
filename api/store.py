"""Storage, API keys, encryption, metering and rate limits for the Taste API.

SQLite (standard library) so it runs anywhere with no setup; swap for Postgres
when hosted. Profiles hold private business numbers (approved claims), so they
are encrypted at rest with Fernet (AES-128-CBC + HMAC) from the cryptography
package. API keys are stored only as SHA-256 hashes.

Defaults are privacy-first: request bodies are never logged, drafts are never
stored (only counts are metered), and nothing is used for training.
"""
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS api_keys (key_hash TEXT PRIMARY KEY, owner TEXT NOT NULL, created REAL NOT NULL,
                                     revoked INTEGER NOT NULL DEFAULT 0, rate_per_min INTEGER NOT NULL DEFAULT 60);
CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, key_hash TEXT NOT NULL, blob BLOB NOT NULL,
                                     created REAL NOT NULL, updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS pending_rules (id TEXT PRIMARY KEY, profile_id TEXT NOT NULL, key_hash TEXT NOT NULL,
                                          rule TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS usage (key_hash TEXT NOT NULL, endpoint TEXT NOT NULL, day TEXT NOT NULL,
                                  calls INTEGER NOT NULL DEFAULT 0, input_tokens INTEGER NOT NULL DEFAULT 0,
                                  output_tokens INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (key_hash, endpoint, day));
"""


def _hash(key):
    return hashlib.sha256(key.encode()).hexdigest()


class Cipher:
    """Encrypts profile blobs. COULIS_ENC_KEY must be a Fernet key in production."""

    def __init__(self, key=None):
        key = key or os.environ.get("COULIS_ENC_KEY")
        self.enabled = bool(key)
        if self.enabled:
            from cryptography.fernet import Fernet
            self.f = Fernet(key.encode() if isinstance(key, str) else key)

    def seal(self, data: bytes) -> bytes:
        return b"F1" + self.f.encrypt(data) if self.enabled else b"P0" + data

    def open(self, blob: bytes) -> bytes:
        tag, body = blob[:2], blob[2:]
        if tag == b"F1":
            if not self.enabled:
                raise RuntimeError("Profile is encrypted but COULIS_ENC_KEY is not set.")
            return self.f.decrypt(body)
        return body

    @staticmethod
    def new_key():
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()


class Store:
    def __init__(self, path=None, cipher=None):
        self.path = path or os.environ.get("COULIS_DB", "coulis.db")
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.executescript(SCHEMA)
        self.lock = threading.Lock()
        self.cipher = cipher or Cipher()
        self.buckets = {}  # key_hash -> (tokens, last_ts) for rate limiting

    # keys
    def create_key(self, owner, rate_per_min=60):
        key = "tst_" + secrets.token_urlsafe(32)
        with self.lock, self.db:
            self.db.execute("INSERT INTO api_keys VALUES (?,?,?,0,?)", (_hash(key), owner, time.time(), rate_per_min))
        return key  # shown once, never stored in plain text

    def auth(self, key):
        if not key:
            return None
        row = self.db.execute("SELECT key_hash, rate_per_min FROM api_keys WHERE key_hash=? AND revoked=0",
                              (_hash(key),)).fetchone()
        return {"key_hash": row[0], "rate_per_min": row[1]} if row else None

    def revoke_key(self, key):
        with self.lock, self.db:
            self.db.execute("UPDATE api_keys SET revoked=1 WHERE key_hash=?", (_hash(key),))

    # rate limit: token bucket per key
    def allow(self, key_hash, rate_per_min):
        now = time.time()
        with self.lock:
            tokens, last = self.buckets.get(key_hash, (float(rate_per_min), now))
            tokens = min(rate_per_min, tokens + (now - last) * rate_per_min / 60.0)
            ok = tokens >= 1
            self.buckets[key_hash] = (tokens - 1 if ok else tokens, now)
        return ok

    # profiles (encrypted)
    def save_profile(self, key_hash, profile_dict, profile_id=None):
        pid = profile_id or "prf_" + uuid.uuid4().hex[:16]
        blob = self.cipher.seal(json.dumps(profile_dict).encode())
        now = time.time()
        with self.lock, self.db:
            self.db.execute("INSERT INTO profiles VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET blob=excluded.blob, "
                            "updated=excluded.updated", (pid, key_hash, blob, now, now))
        return pid

    def load_profile(self, key_hash, pid):
        row = self.db.execute("SELECT blob FROM profiles WHERE id=? AND key_hash=?", (pid, key_hash)).fetchone()
        return json.loads(self.cipher.open(row[0])) if row else None

    def delete_profile(self, key_hash, pid):
        with self.lock, self.db:
            n = self.db.execute("DELETE FROM profiles WHERE id=? AND key_hash=?", (pid, key_hash)).rowcount
            self.db.execute("DELETE FROM pending_rules WHERE profile_id=? AND key_hash=?", (pid, key_hash))
        return bool(n)

    # rules awaiting human approval (encrypted too: rules quote drafts)
    def add_pending(self, key_hash, pid, rule_text):
        rid = "rul_" + uuid.uuid4().hex[:16]
        with self.lock, self.db:
            self.db.execute("INSERT INTO pending_rules VALUES (?,?,?,?,?)",
                            (rid, pid, key_hash, self.cipher.seal(rule_text.encode()), time.time()))
        return rid

    def pop_pending(self, key_hash, rid):
        row = self.db.execute("SELECT profile_id, rule FROM pending_rules WHERE id=? AND key_hash=?",
                              (rid, key_hash)).fetchone()
        if not row:
            return None
        with self.lock, self.db:
            self.db.execute("DELETE FROM pending_rules WHERE id=?", (rid,))
        return row[0], self.cipher.open(row[1]).decode()

    # metering: counts only, never content
    def meter(self, key_hash, endpoint, input_tokens=0, output_tokens=0):
        day = time.strftime("%Y-%m-%d", time.gmtime())
        with self.lock, self.db:
            self.db.execute("INSERT INTO usage VALUES (?,?,?,1,?,?) ON CONFLICT(key_hash,endpoint,day) DO UPDATE SET "
                            "calls=calls+1, input_tokens=input_tokens+excluded.input_tokens, "
                            "output_tokens=output_tokens+excluded.output_tokens",
                            (key_hash, endpoint, day, input_tokens, output_tokens))

    def usage(self, key_hash):
        rows = self.db.execute("SELECT endpoint, day, calls, input_tokens, output_tokens FROM usage WHERE key_hash=? "
                               "ORDER BY day DESC, endpoint", (key_hash,)).fetchall()
        return [dict(zip(("endpoint", "day", "calls", "input_tokens", "output_tokens"), r)) for r in rows]
