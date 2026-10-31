#!/usr/bin/env python3
"""coulis shadow mode for a Slack channel: read drafts, run the gate, log results. Posts nothing.

    python3 examples/slack_shadow.py --env ~/.coulis/secrets/slack.env \
        --profile ~/clients/acme --out ~/.coulis/shadow/acme
    python3 examples/slack_shadow.py ... --digest          # print what it would have caught, by day

The .env file holds two lines: SLACK_BOT_TOKEN=xoxb-...  and  SLACK_CHANNEL=C...
Needs a bot with channels:history + channels:read (or groups:* for a private channel). Read-only.
State: <out>/state.json (last timestamp seen), <out>/log.jsonl (one line per draft checked),
<out>/pairs.jsonl (draft vs edited version, for learn).
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coulis_core import check, learn, profile_from_folder  # noqa: E402

MIN_WORDS = 20


def load_env(path):
    env = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def slack(token, method, **params):
    url = "https://slack.com/api/" + method + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if not data.get("ok"):
        raise SystemExit(f"Slack error on {method}: {data.get('error')}")
    return data


def fetch(token, channel, oldest):
    msgs, cursor = [], None
    while True:
        params = {"channel": channel, "limit": 200, "oldest": oldest or "0", "inclusive": "false"}
        if cursor:
            params["cursor"] = cursor
        d = slack(token, "conversations.history", **params)
        msgs += d.get("messages", [])
        cursor = d.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return sorted(msgs, key=lambda m: float(m["ts"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--surface", default="reddit")
    ap.add_argument("--digest", action="store_true", help="print the digest and exit")
    a = ap.parse_args()
    out = Path(os.path.expanduser(a.out))
    out.mkdir(parents=True, exist_ok=True)
    log_path, pairs_path, state_path = out / "log.jsonl", out / "pairs.jsonl", out / "state.json"
    rows = [json.loads(l) for l in log_path.read_text().splitlines()] if log_path.exists() else []

    if a.digest:
        by_day = {}
        for r in rows:
            d = by_day.setdefault(r["date"], {"drafts": 0, "Hold": 0, "Revise": 0, "Send": 0, "issues": {}})
            d["drafts"] += 1
            d[r["verdict"]] += 1
            for i in r["issues"]:
                d["issues"][i["check"]] = d["issues"].get(i["check"], 0) + 1
        for day, d in sorted(by_day.items()):
            print(f"{day}: {d['drafts']} drafts, {d['Hold']} would be stopped, {d['Revise']} sent back, {d['Send']} passed. Caught: {d['issues']}")
        pairs = pairs_path.read_text().count("\n") if pairs_path.exists() else 0
        print(f"{len(rows)} drafts checked in total, {pairs} draft/edit pairs saved for learn.")
        return

    env = load_env(os.path.expanduser(a.env))
    token, channel = env["SLACK_BOT_TOKEN"], env["SLACK_CHANNEL"]
    profile = profile_from_folder(os.path.expanduser(a.profile))
    state = json.loads(state_path.read_text()) if state_path.exists() else {"last_ts": "0", "seen": {}}

    msgs = fetch(token, channel, state["last_ts"])
    new = 0
    for m in msgs:
        text = (m.get("text") or "").strip()
        ts = m["ts"]
        if len(text.split()) < MIN_WORDS:
            continue
        when = dt.datetime.fromtimestamp(float(ts))
        # the client's own posts from the last 7 days are the history for the sameness check
        recent = [r for r in rows if 0 <= (when - dt.datetime.fromisoformat(r["ts_iso"])).days <= 7]
        hist = [{"id": r["slack_ts"], "date": r["date"], "title": r["preview"], "text": r["text"]} for r in recent]
        res = check(text, profile, a.surface, hist)
        row = {"slack_ts": ts, "ts_iso": when.isoformat(timespec="seconds"), "date": when.date().isoformat(),
               "user": m.get("user") or m.get("bot_id", "?"), "words": len(text.split()),
               "preview": " ".join(text.split()[:12]), "text": text, "verdict": res["verdict"], "issues": res["issues"]}
        rows.append(row)
        with log_path.open("a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        state["seen"][ts] = text
        state["last_ts"] = ts
        new += 1

    # edits: Slack returns the current text; if a message we saw before now reads differently, save the pair
    edited = 0
    if state["seen"]:
        oldest = min(state["seen"], key=float)
        for m in fetch(token, channel, str(float(oldest) - 1)):
            old = state["seen"].get(m["ts"])
            cur = (m.get("text") or "").strip()
            if old and cur and cur != old:
                rules = learn(old, cur, profile)["proposed_rules"]
                with pairs_path.open("a") as f:
                    f.write(json.dumps({"slack_ts": m["ts"], "draft": old, "final": cur,
                                        "proposed_rules": [r["text"] for r in rules]}, ensure_ascii=False) + "\n")
                state["seen"][m["ts"]] = cur
                edited += 1
    state_path.write_text(json.dumps(state))
    print(f"{dt.datetime.now():%Y-%m-%d %H:%M} checked {new} new draft(s), saved {edited} edit pair(s). Posted nothing.")


if __name__ == "__main__":
    main()
