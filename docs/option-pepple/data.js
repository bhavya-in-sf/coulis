window.PEPPLE_ASSETS = {
  "brand": "pepple",
  "intro": "We bring you back.",
  "quotes": [{"quote":"","name":"","role":""}],
  "patterns": [
    {"label": "Stock opening", "text": "Thrilled to announce our next chapter.", "kind": "serif"},
    {"label": "Vague promise", "text": "Everything you need. All in one place.", "kind": "rounded"},
    {"label": "Unapproved number", "text": "Your team. Now 10x faster.", "kind": "accent"},
    {"label": "Filler", "text": "Unlock your potential.", "kind": "pulse"},
    {"label": "Generic headline", "text": "The future of work starts here.", "kind": "headline"},
    {"label": "Repeated idea", "text": "A better way to work. A smarter way to work.", "kind": "nested"},
    {"label": "Interchangeable claims", "text": "Create. Connect. Grow.", "kind": "trio"},
    {"label": "Repeated hook", "text": "Discover. Build. Transform.", "kind": "steps"}
  ],
  "console": {
    "title": "Check this draft",
    "before": "We are thrilled to unveil a game-changing tool that makes every team 10x faster.",
    "after": "We built a check for AI drafts. It compares each line with your approved facts and your voice.",
    "checks": [
      {"name": "Facts", "note": "Quotes numbers and claims that are not in your approved facts."},
      {"name": "Voice", "note": "Quotes words and phrases you asked to avoid."},
      {"name": "Clarity", "note": "Names the line that needs a clearer meaning."},
      {"name": "Rhythm", "note": "Flags repeated openings and sentence patterns."}
    ]
  },
  "agent": {"request": "", "response": "", "steps": [""], "quote": "", "instruction": ""},
  "live": {"title": "", "lines": [""], "notes": [""]},
  "worlds": [{"name":"","category":"","title":"","color":"#fff","ink":"#000"}],
  "case": {"eyebrow":"","title":"","body":"","caption":""},
  "terminal": {
    "title": "What one check looks like",
    "lines": [
      "Loading your approved facts",
      "Loading your voice file",
      "The gate: fixed rules, no AI model, about 4 ms",
      "Quoted: “10x faster” is not in your approved facts",
      "The critique: 8 things scored separately, weakest line rewritten",
      "Your decision. Nothing is saved without your yes."
    ]
  },
  "file": {
    "name": "TASTE.md",
    "lines": [
      "# Your facts",
      "62K LinkedIn followers",
      "LinkedIn Top Voice 2024",
      "",
      "# Your voice",
      "Open with the concrete thing you built.",
      "Avoid: game-changer, seamless, leverage.",
      "",
      "# Learned, with your approval",
      "Lead with a number, not a question."
    ]
  },
  "specimen": {"name":"","swatches":["#fff"],"font":"Aa","principle":"","rules":[""]},
  "modes": [
    {"name": "LAUNCH POST", "title": "What did you build?"},
    {"name": "COLD EMAIL", "title": "Why this person?"},
    {"name": "INVESTOR UPDATE", "title": "What changed, in numbers?"},
    {"name": "BIO", "title": "Who are you, in one line?"}
  ],
  "pipeline": [
    {"title": "1. The gate", "detail": "Fixed rules, no AI model, same answer every time"},
    {"title": "2. The critique", "detail": "8 things scored separately, weakest line rewritten"},
    {"title": "3. The learning", "detail": "Your edit becomes a proposed rule"},
    {"title": "You approve", "detail": "Your taste file grows. You own it."}
  ],
  "install": {
    "platforms": ["Claude Code", "Claude Desktop", "Cursor"],
    "command": "/plugin marketplace add bhavya-in-sf/sauce",
    "steps": [
      {"title": "Add the plug-in", "body": "In Claude Code run /plugin marketplace add bhavya-in-sf/sauce, then /plugin install sauce@sauce. (Working package name while the brand name is decided.)"},
      {"title": "Build your taste file", "body": "Run /sauce:extract on your past posts or LinkedIn export. Confirm each fact before it counts."},
      {"title": "Check a draft", "body": "Write as usual. Each quoted issue waits for your decision before anything goes out."}
    ]
  },
  "integrations": ["Claude Code", "Claude Desktop", "Cursor", "MCP clients"],
  "footer": "Your facts. Your voice. Your taste."
};
