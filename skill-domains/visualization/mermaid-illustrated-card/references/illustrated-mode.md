# Illustrated mode — keep the exact Mermaid semantics

Use this only when an image-generation tool is actually available. The deterministic SVG renderer already creates a consistent mint editorial card with vector connectors, labels and small line icons.

## Workflow

1. Read the uploaded Mermaid, lock all nodes/edges/branch labels/directions/subgraphs using `fidelity.md`.
2. Inspect the eight separate cropped references under `../examples/reference-cards/` to understand the **shared design system** (white card + mint title bar + gray outline + teal nodes). Pick only a composition type that accurately represents the source Mermaid.
3. Render exact diagram geometry and text in SVG (native Mermaid or bundled deterministic renderer) **before** any artistic enhancements.
4. If useful, generate **decorative icon/background elements only** in the user-specified style; keep arrows, text, stage connections, branch labels and node IDs in deterministic vector overlays.
5. Composite and inspect the final 1024×1024 card. Reject any changed flow, missing text, bad connections, incorrect node labels, or small unreadable type.

## Decoration-only generation prompt

> Create a **square 1:1 editorial technical learning card illustration layer**, visually consistent with eight white-background mint-green infographic reference cards. White base, bright teal/mint rounded title banner (`#2ED9AA`), thin soft gray border (`#B8BFBE`), sparse original line-art icons, soft mint/aqua pastel fills (`#2DD9A9`, `#BFFFF0`, `#E6FFF7`), crisp near-black outlines and plenty of white space. Neat, compact, flat 2D illustration, restrained color palette, readable and professional. Leave diagram region free for later vector overlay. **Do not draw text, arrows, new boxes, decisions, graph edges, logos, or steps**. Avoid photorealism, gradients, shadows, and the full-bleed rainbow card variants.

When vector compositing is impossible and a one-shot image must be made, supply the exact Mermaid node and edge inventory verbatim and reject any drawing that deviates. Prefer a slightly less embellished but correct vector diagram to a more attractive but incorrect image.
