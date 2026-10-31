# coulis for OpenClaw

The same check as the Claude plug-in, as an OpenClaw skill. Deterministic, local, no model call.

Install:
```
clawhub install coulis
```
or copy `openclaw/coulis/` into `~/.openclaw/skills/coulis/` and clone this repo into `~/.openclaw/skills/coulis/repo`.

The skill tells the agent to run `scripts/coulis.py check` before any post, email or message that goes out under the owner's name, and what to do with BLOCK, FIX and PASS. See `coulis/SKILL.md`.

Publishing to ClawHub (owner only): `clawhub publish openclaw/coulis`.


Taste memory now runs inside the existing CLI and agent workflow: retrieve context before drafting, record permitted edits or choices, and approve preferences explicitly. See [shared workflow](../docs/TASTE-LOOP.md). No separate web workspace is needed.
