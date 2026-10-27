# sauce for OpenClaw

The same check as the Claude plug-in, as an OpenClaw skill. Deterministic, local, no model call.

Install:
```
clawhub install sauce
```
or copy `openclaw/sauce/` into `~/.openclaw/skills/sauce/` and clone this repo into `~/.openclaw/skills/sauce/repo`.

The skill tells the agent to run `scripts/sauce.py check` before any post, email or message that goes out under the owner's name, and what to do with BLOCK, FIX and PASS. See `sauce/SKILL.md`.

Publishing to ClawHub (owner only): `clawhub publish openclaw/sauce`.
