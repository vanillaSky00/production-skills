# Mermaid Illustrated Card — Agent Skill (v2)

Convert a user-supplied Mermaid diagram to a **fixed-size 1024×1024** technical teaching card. Default art style: **white background, rounded thin-gray card border, vivid mint title bar, soft teal diagram shapes, black labels/arrows, small icons**.

**Install:** Place the entire `mermaid-illustrated-card` directory in an Agent Skills directory, such as `~/.agents/skills/` (Codex) or `~/.claude/skills/` (Claude Code). Ensure the `SKILL.md` stays at the top of the folder.

```bash
pip install -r requirements.txt
# Also install Graphviz `dot` (e.g. brew install graphviz or apt install graphviz).
python scripts/render_card.py --mermaid examples/agent-research.mmd --out card.png --theme mint-editorial
python scripts/check_card.py card.png
```

**Reference gallery:** The 8 individual style-reference crops are under `examples/reference-cards/`, each **468×468 px** native from the uploaded screenshot. **Finished renders always use 1024×1024** by default. `examples/mint-editorial-demo.png` is a generated output of a Mermaid diagram, not a crop.

**Other color themes** (full-bleed mint, sky, peach, lavender, lime, pink) are optional, not the default. See `SKILL.md` and `references/style-guide.md` for the contract and detailed rules.
