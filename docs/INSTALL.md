# Install Coulis Preview

This installs the local experimental tools, not a trained Coulis taste LLM. The model is in research; hosted model/API access remains waitlist only.

Coulis runs anywhere that supports MCP. You need Python 3.10+ (already on most Macs: check with `python3 --version`). No API key: the critique runs on the model you're already chatting with.

## 1. Get the code
```bash
git clone https://github.com/bhavya-in-sf/coulis ~/coulis
```

## 2. Make a folder for your taste profile
Coulis reads `TASTE.md` (samples and broad preferences), `preferences.json` (approved scoped rules), and `claims.json` (complete claim approvals) from one folder. Legacy `claims.md` notes remain readable but no longer clear numbers by themselves.
```bash
mkdir -p ~/coulis-profile
```
Leave it empty. Ask Claude to "set up my Coulis profile" and approve the proposed profile entries. To try the real demo profile first, use `~/coulis/personas/bhavya` instead.

## 3. Connect your app

### Claude Code
```
/plugin marketplace add bhavya-in-sf/coulis
/plugin install coulis@coulis
```
The plug-in adds the commands (`/coulis:setup`, `/coulis:critique`, `/coulis:learn`, `/coulis:gate`) and starts the MCP tools. It uses the folder you're working in as the profile folder.

### Claude Desktop
Open **Settings → Developer → Edit Config** (this opens `claude_desktop_config.json`) and add:
```json
{
  "mcpServers": {
    "coulis": {
      "command": "python3",
      "args": ["/Users/YOU/coulis/mcp/server.py"],
      "env": { "COULIS_PROFILE_DIR": "/Users/YOU/coulis-profile" }
    }
  }
}
```
Replace `YOU` with your Mac username (run `whoami`), save, and restart Claude Desktop.

### Cursor
Open **Settings → MCP → Add new MCP server**, or edit `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "coulis": {
      "command": "python3",
      "args": ["/Users/YOU/coulis/mcp/server.py"],
      "env": { "COULIS_PROFILE_DIR": "/Users/YOU/coulis-profile" }
    }
  }
}
```

### Any other MCP app
Command `python3`, argument `/path/to/coulis/mcp/server.py`, environment variable `COULIS_PROFILE_DIR` set to your profile folder. Transport is stdio.

## 4. Use it
Just ask in plain words:
- "Check this draft with Coulis: ..." → `coulis_check` (instant, no model call)
- "Critique this with Coulis" → `coulis_critique` (8 axes, rewrites the weakest part)
- "Approve this complete claim record" → `coulis_approve_claim`; see [the schema](PRODUCT.md). Personal phrase bans use `coulis_add`.
- "Here's the AI draft and what I posted, learn from it" → `coulis_learn` (you approve each rule)

## Troubleshooting
- **Tools don't show up:** check that the path in `args` is right (`ls /Users/YOU/coulis/mcp/server.py`) and restart the app.
- **Every number gets flagged:** numeric wording needs a complete, active approval in `claims.json`. Use `coulis_approve_claim` after checking the source and wording. Unknown paraphrases stay unresolved.
- **`python3` not found:** install Python from python.org, or use the full path (`which python3`).

### Hosted integrations
Hosted model/API access and managed integrations are waitlist only. The local Python/MCP prototype does not provision a remote service. [Paid design-partner scope](BUSINESS.md).
