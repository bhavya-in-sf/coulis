# Install Tastee

Tastee runs anywhere that supports MCP. You need Python 3.10+ (already on most Macs: check with `python3 --version`). No API key: the critique runs on the model you're already chatting with.

## 1. Get the code
```bash
git clone https://github.com/bhavya-in-sf/tastee ~/tastee
```

## 2. Make a folder for your taste profile
Tastee reads `TASTE.md` (your style) and `claims.md` (numbers you're happy to post) from one folder.
```bash
mkdir -p ~/tastee-profile
```
Leave it empty. Ask Claude to "set up my Tastee profile" and it will fill both files. To try the real demo profile first, use `~/tastee/personas/bhavya` instead.

## 3. Connect your app

### Claude Code
```
/plugin marketplace add bhavya-in-sf/tastee
/plugin install tastee@tastee
```
The plug-in adds the commands (`/tastee:setup`, `/tastee:critique`, `/tastee:learn`, `/tastee:gate`) and starts the MCP tools. It uses the folder you're working in as the profile folder.

### Claude Desktop
Open **Settings → Developer → Edit Config** (this opens `claude_desktop_config.json`) and add:
```json
{
  "mcpServers": {
    "tastee": {
      "command": "python3",
      "args": ["/Users/YOU/tastee/mcp/server.py"],
      "env": { "TASTEE_PROFILE_DIR": "/Users/YOU/tastee-profile" }
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
    "tastee": {
      "command": "python3",
      "args": ["/Users/YOU/tastee/mcp/server.py"],
      "env": { "TASTEE_PROFILE_DIR": "/Users/YOU/tastee-profile" }
    }
  }
}
```

### Any other MCP app
Command `python3`, argument `/path/to/tastee/mcp/server.py`, environment variable `TASTEE_PROFILE_DIR` set to your profile folder. Transport is stdio.

## 4. Use it
Just ask in plain words:
- "Check this draft with Tastee: ..." → `tastee_check` (instant, no model call)
- "Critique this with Tastee" → `tastee_critique` (8 axes, rewrites the weakest part)
- "Add '1,200 users' as an approved fact" or "Ban the phrase 'game-changer'" → `tastee_add`
- "Here's the AI draft and what I posted, learn from it" → `tastee_learn` (you approve each rule)

## Troubleshooting
- **Tools don't show up:** check that the path in `args` is right (`ls /Users/YOU/tastee/mcp/server.py`) and restart the app.
- **Every number gets flagged:** your `claims.md` has no approved facts yet. Add them with `tastee_add`.
- **`python3` not found:** install Python from python.org, or use the full path (`which python3`).
