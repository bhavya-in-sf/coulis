window.PEPPLE_HERO = {
  "brand": "pepple",
  "headline": "We bring\nyou back.",
  "description": "AI learned everyone. Pepple teaches it you: your facts, your voice, your taste, in a file you own. It checks AI drafts before they go out under your name.",
  "primaryLabel": "Try the plug-in",
  "primaryHref": "#install",
  "secondaryLabel": "How it works",
  "secondaryHref": "#how",
  "integrations": ["Claude Code", "Claude Desktop", "Cursor"],
  "examples": [
    {
      "tab": "/facts", "title": "Check your facts", "document": "LAUNCH POST",
      "beforeTitle": "A game-changer for every team.",
      "beforeBody": "Our new tool makes teams 10x faster. The future of work starts here.",
      "afterTitle": "We built a check for AI drafts.",
      "afterBody": "It quotes claims that are missing from your approved facts. You decide what goes out.",
      "beforeFooter": "Draft awaiting review", "afterFooter": "Example of a human-approved edit",
      "notes": [{"label":"Banned phrase","top":26},{"label":"Unapproved claim","top":51},{"label":"Generic ending","top":72}],
      "rule": "Flag numbers and claims that are not in my approved facts."
    },
    {
      "tab": "/voice", "title": "Keep your voice", "document": "FOUNDER UPDATE",
      "beforeTitle": "Thrilled to announce our next chapter.",
      "beforeBody": "We are delighted to unveil a seamless experience that empowers your creative journey.",
      "afterTitle": "This is what we have been working on.",
      "afterBody": "A place for your facts and writing preferences, so you stop explaining yourself from scratch.",
      "beforeFooter": "Draft awaiting review", "afterFooter": "Example of a human-approved edit",
      "notes": [{"label":"Stock opening","top":27},{"label":"Not your words","top":52},{"label":"Too much filler","top":74}],
      "rule": "Use direct openings. Avoid thrilled, seamless and empower."
    },
    {
      "tab": "/taste", "title": "Learn what you approve", "document": "YOUR TASTE FILE",
      "beforeTitle": "You make the same edit again.",
      "beforeBody": "Another big opening. Another vague promise. Another draft that needs the same feedback.",
      "afterTitle": "Your edit becomes a proposed rule.",
      "afterBody": "Open with the concrete thing we built. Saved only after you approve it.",
      "beforeFooter": "A repeated preference", "afterFooter": "Illustrative rule, approved by you",
      "notes": [{"label":"Repeated edit","top":28},{"label":"Vague promise","top":52},{"label":"Not remembered","top":74}],
      "rule": "Propose a rule from my edits. Ask before adding it to my file."
    }
  ]
};
