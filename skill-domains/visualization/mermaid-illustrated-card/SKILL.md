---
name: mermaid-illustrated-card
description: Turn an uploaded Mermaid diagram (.mmd, .mermaid, Markdown Mermaid code block, or pasted Mermaid) into a consistent fixed-size square technical illustration card using the white-background mint/teal editorial style shown in the bundled eight reference cards. Use when asked to visualize a Mermaid diagram as an infographic, system-design card, architecture card, or colorful flowchart. Preserve node labels, edges, branches, loops, groups, and direction while simplifying only presentation. 將 Mermaid 流程圖轉成 1024×1024 彩色教學圖卡、系統架構卡片；保持節點與箭頭正確。
compatibility: Python 3, Graphviz dot for deterministic flowcharts. PNG rendering optionally requires cairosvg. Optional Mermaid CLI or image-generation tool for complex/illustrated variants.
---

# Mermaid → Illustrated Technical Card

## Mission

Take a Mermaid diagram from the current user message or attached file and **deliver the finished image**, not just a prompt or diagram explanation. Make one consistently sized **1024 × 1024 px (1:1)** educational card, with clean technical diagrams, a white card, bright mint-green rounded title banner, subtle gray outer border, charcoal connectors, soft mint/aqua nodes, and small semantic line icons. The user-provided Mermaid is the **source of truth**, never a vague artistic reference.

**Primary visual examples (8 individual crops):** `examples/reference-cards/01-resume-review.png` through `08-generative-ai-system.png`. These were cropped from the user's new 2×4 reference collage and are meant to be browsed **individually**. For the full list and design cues, read [reference cards README](examples/reference-cards/README.md) and [style guide](references/style-guide.md). Retain their common **color family and structure**, not their specific diagrams, trademarks, typography assets, text, characters, or logos. Alternate saturated card samples are in `assets/reference-*.jpg` and may be used **only when the user chooses an alternate theme**.

## Non-negotiable constraints (in priority order)

1. **Semantic fidelity beats decoration.** Preserve every source node, exact node meaning, arrows, directionality, edge labels, yes/no branches, cycles, and subgraph membership. A beautiful incorrect diagram is a failed result. Never invent a step, dependency, metric, label, or edge.
2. **Legibility beats compactness.** Prefer fewer decorative details, shorter line wraps (not rewriting labels), consistent font sizes, clean connectors, generous whitespace. Do not silently drop nodes to fit.
3. **One reusable card system.** Fixed output **1024×1024**, **white rounded canvas**, very thin gray outer border, **mint/teal rounded title banner**, large 1–2-line black heading, simple white/pale-mint diagram area, charcoal connectors, 2–3 coordinated teal/mint shades, small line icons. **Use this same palette for every card in a series**; do not randomly switch to orange/purple backgrounds. The 8 cropped reference cards are square but source-resolution (468×468); they are *references*, not output-size templates.
4. **Simplify the layout, not the graph.** Rearrange node positions, group logically, replace generic rectangles with suitable simple shapes and icons, but retain Mermaid topology and wording. Do not translate or paraphrase labels without request.
5. **Keep the card itself the output.** No unrelated paragraphs inside the artwork, no footnotes, no watermark, no mock UI, no stacked 16:9 pages, no brand logo.

## Input and defaults

- Accept `.mmd`, `.mermaid`, `.md` with fenced `mermaid`, or pasted Mermaid code.
- Optional user overrides: `title`, theme (`mint-editorial` default; optional classic `mint`, `sky`, `peach`, `lavender`, `lime`, `pink`), size (only if explicitly changed), output format, and number of cards.
- Default output: **one 1024×1024 PNG + an editable SVG**. **Always use `mint-editorial` by default**, regardless of topic, matching the user-supplied 8-card collection. For multiple cards, keep the *same* default palette. Change themes only when explicitly asked.
- If no title provided, use `%% title: ...` from Mermaid or derive a concise, accurate title from the diagram. Never fabricate new topical claims.
- A single uploaded Mermaid means a **single card** unless the user explicitly asks for a series. When very dense, preserve all relationships and state if readability cannot be achieved at the fixed size.

## Workflow

### 1. Extract and lock the diagram contract

Before drawing, read the source completely and inventory the information in [fidelity checklist](references/fidelity.md):

- Mermaid type and layout direction (`TB`, `LR`, etc.).
- Node IDs, exact display labels, semantic shapes.
- All directed/undirected edges and their from/to endpoints.
- All edge labels (`Yes`, `No`, errors, percentages) and feedback paths.
- Subgraphs, nesting, swimlanes/participants and visible ordering.

Use the contract as an internal checklist. **Do not ask the user to retype Mermaid already provided.** Do not infer new connections.

### 2. Select a fidelity-safe renderer

**Path A — most ordinary `flowchart` / `graph` diagrams (preferred):**

Run the bundled deterministic renderer. It creates the colorful illustration card as SVG and PNG, with actual vector lines, arrows, labels, and icons (not AI-guessed connectors):

```bash
python scripts/render_card.py --mermaid ./input.mmd --out ./output/card.png --theme mint-editorial
python scripts/check_card.py ./output/card.png
```

The parser deliberately supports a **strict subset** of Mermaid flowcharts: basic nodes, shapes, chains, labeled edges, back edges, and non-nested subgraphs. It **fails loudly** for unsupported structural Mermaid instead of silently inventing a graph. See `examples/agent-research.mmd` and `examples/grouped.mmd`.

**Path B — unsupported advanced flowchart features:**

Build a **lossless** JSON graph spec with node IDs, labels, edges, edge labels, direction, optional groups and shapes; use `examples/agent-research.json` as the schema example. Compare the resulting spec against the source before rendering:

```bash
python scripts/render_card.py --spec ./diagram.json --out ./output/card.png --theme mint-editorial
```

Only choose this when the original topology can be represented faithfully. Do not flatten a nested/grouped/semantic diagram if its meaning would be lost.

**Path C — other Mermaid types (e.g. `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`, `gantt`, `gitGraph`) or advanced syntax:**

Use the actual Mermaid engine to render the SVG first, then place the **native SVG** within the square illustrated card so the source diagram remains correct. If Mermaid CLI is installed:

```bash
mmdc -i ./input.mmd -o ./output/mermaid-native.svg -b transparent -c assets/mermaid-config.json
python scripts/wrap_mermaid_svg.py --svg ./output/mermaid-native.svg --title 'Diagram Title' --theme mint-editorial --out ./output/card.png
```

For Mermaid generated with HTML/`foreignObject` labels, use a renderer/browser that supports them to export the native diagram; do not accept missing labels from an SVG converter. If the native content is too dense, adjust layout/label wrapping or produce SVG for zooming. Do not misrepresent it as legible at card size.

### 3. Add visual polish without corrupting the diagram

Read [style guide](references/style-guide.md) and look at **all eight** `examples/reference-cards/*.png` in the current style family. Match **white canvas + thin light-gray outline + strong mint title bar**; nodes in pastel mint/teal/aqua/white; black type and thin charcoal connectors; semantic icons typically 18–36px. Use illustrated detail sparingly, not a rainbow palette. Match an example's **diagram archetype** (pipeline, annotated document, multi-panel explainer, mind map, UML, UI architecture, feedback loop) **only when that structure is faithful to the uploaded Mermaid**. If the reference depicts steps Mermaid does not contain, do not add them.

If an image-generation tool is available and the user wants a **more illustrated/art-directed** card, follow [illustrated mode](references/illustrated-mode.md) using the same mint/teal reference palette. Keep vector-rendered connectors and text as the source of truth. Image generation may create decorative backgrounds or icon assets, but **must not rewrite or rewire the diagram**. If you cannot reliably composite those layers, deliver the deterministic card instead of an inaccurate raster drawing.

### 4. Mandatory QA and delivery

- Run `scripts/check_card.py` to verify PNG size and nonblank output. Every delivered output card should be 1024×1024 unless the user explicitly requests a consistent different square size.
- Visually inspect the **actual exported image**, not just the SVG source. Check labels, icons, clipping, arrowheads, overlap, and contrast.
- Compare the output against the locked contract: same nodes, same connections, same branch labels, same grouping. Specifically check cycle/feedback paths.
- If a branch label is on the wrong connector or any node disappears, fix and rerender. Never declare fidelity after only checking dimensions.
- Deliver the actual PNG and, when produced, SVG. Optionally provide the JSON spec for future edits. Tell the user when a complex Mermaid feature could not be preserved.

## Quick usage examples

**Prompt:** "Turn this Mermaid into a 1024×1024 white-and-mint system-design card. Use the same green title bar, soft teal nodes and thin gray border as examples/reference-cards. Keep every dependency." Attach `.mmd`.

**Prompt:** "把這個 Mermaid 做成和 ByteByteGo 那種彩色教學卡片一樣，1:1、1024×1024、小圖示、不要改流程，使用 mint-editorial 薄荷綠配色。" Attach Mermaid or paste a fenced block.

**Output layout:** `card.png` (finished card, 1024×1024), `card.svg` (editable vector), optional `diagram.json` (verifiable source topology).

**Files to inspect for inspiration:**

- `examples/reference-cards/01-resume-review.png` — annotation layout
- `examples/reference-cards/02-coding-patterns.png` — divided small diagram panels
- `examples/reference-cards/03-system-design.png` — staged process/swimlanes
- `examples/reference-cards/04-behavioral-interview.png` — mind map
- `examples/reference-cards/05-object-oriented-design.png` — UML/class relationships
- `examples/reference-cards/06-machine-learning-system.png` — pipeline stages
- `examples/reference-cards/07-mobile-system-design.png` — component architecture
- `examples/reference-cards/08-generative-ai-system.png` — feedback loop / agent system

**Illustrated result sample from bundled Mermaid:** `examples/mint-editorial-demo.png`. The eight crops are supplied **visual examples only**; they do not carry Mermaid semantics or code.

## Dependencies and limits

- `python3` and `dot` from Graphviz required for deterministic flowcharts.
- `pip install cairosvg pillow` for PNG output and file QA. SVG can be produced without CairoSVG.
- Optional: `mmdc` (Mermaid CLI) for native rendering of advanced Mermaid.
- This skill provides a reliable **card composition system**. The exact designerly quality of a bespoke illustration varies with the availability of an image-generation tool; the deterministic SVG version favors fidelity and crispness.
