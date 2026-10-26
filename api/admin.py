#!/usr/bin/env python3
"""Admin CLI for the Taste API.

    python3 api/admin.py new-enc-key            # generate SAUCE_ENC_KEY (store it in a secret manager)
    python3 api/admin.py create-key --owner acme --rate 60
    python3 api/admin.py revoke-key tst_...
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api.store import Cipher, Store  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("new-enc-key")
    c = sub.add_parser("create-key")
    c.add_argument("--owner", required=True)
    c.add_argument("--rate", type=int, default=60, help="requests per minute")
    r = sub.add_parser("revoke-key")
    r.add_argument("key")
    a = ap.parse_args()
    if a.cmd == "new-enc-key":
        print(Cipher.new_key())
    elif a.cmd == "create-key":
        print(Store().create_key(a.owner, a.rate))
        print("Shown once. Only a hash is stored.", file=sys.stderr)
    else:
        Store().revoke_key(a.key)
        print("Revoked.")


if __name__ == "__main__":
    main()
