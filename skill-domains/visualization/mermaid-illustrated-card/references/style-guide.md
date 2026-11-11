# Visual system: white + mint technical learning cards (default)

## Study the eight reference cards, not just the collage

All 8 individual square crops are in [`../examples/reference-cards/`](../examples/reference-cards/). They are consistent in design language but support different diagram compositions. Inspect all of them as visual references, then choose the composition that matches the **actual Mermaid structure**. Do not copy the sample wording, logos, icons, or graph topology. The cropped images are **468×468 px** because that is their original source resolution; **generated cards must be 1024×1024 px** unless the user explicitly changes the whole series size.

## Default `mint-editorial` design tokens

| Element | Token | Guidance |
|---|---|---|
| Canvas | `#FFFFFF` | White background; single square image, not a collage |
| Outer border | `#B8BFBE` | Thin 2–3px soft gray, ~60–65px rounded corners |
| Title bar | `#2ED9AA` | Large rounded mint-green banner, full width minus ~50px margins |
| Main text | `#172222` | Black/charcoal sans serif, bold for titles |
| Primary node | `#2DD9A9` | Strong mint used in a few significant stages |
| Secondary node | `#BFFFF0` | Soft mint/aqua background |
| Tertiary node | `#E6FFF7` | Near-white pale green |
| Optional accent | `#88EACA` | Muted teal; do not randomly add purple, orange and yellow |
| Diagram interior | `#FFFFFF` or `#E7FFF5` | Mostly white; pale panel when group/swimlane helps reading |
| Connectors | `#172222` | Thin, dark, arrows point accurately |

### Layout proportions on a 1024×1024 card

- **Outer card**: 1:1 square, 3px light gray stroke, rounded radius about 65px. Never crop card corners.
- **Top title banner**: x≈51, y≈44, width≈922; height≈145 for one-line or ≈180 for two-line titles; corner radius ≈46px. Title center aligned with visually balanced 44–62px black heavy sans-serif.
- **Diagram**: starts ≈25–30px below banner; 50–85px horizontal margins. Use whitespace around structure. A plain white diagram area is often preferable to a visible inset board.
- **Nodes**: compact rectangular pills/boxes and semantic shapes, dark 2–3px outline. Mint fills from the same tonal family. Avoid large drop shadows and heavy gradients.
- **Connections**: dark 2.5–3.5px lines, clear arrowheads and correct direction; feedback loops should go around nodes rather than through labels.
- **Small icons**: 18–36px simple original line-art. One semantic icon per stage when useful, no random decoration. Use no unverified brand logos.
- **Body labels**: strive for 21–30px at final 1024 output and preserve exact Mermaid label text. If unreadable, improve graph layout rather than omitting or abbreviating content.
- **Diagrams with subgraphs**: use pale mint fill or fine dashed border to distinguish groups **only if Mermaid actually has groups**.

## Eight reference diagrams and their layout cues

1. Resume review: small annotations layered on a document-like panel.
2. Coding patterns: 2×2 teaching cells with tiny diagrams.
3. System design: staged swimlanes, numbers, small pictograms and dotted connectors.
4. Behavioral interview: mind map with branching boxes.
5. Object-oriented design: UML-like hierarchy and interfaces, thin directional arrows.
6. Machine learning system: left-to-right pipeline, simple offset box/stage geometry.
7. Mobile system design: a high-level container connected to compact child components.
8. Generative AI system: intentional cycle showing user, generation, reflection and output.

**Important:** These are style/composition examples. Do not render a UML diagram just because you like example 5; use the actual Mermaid type. **Preserve topology first.** Do not invent nodes, branches or labels to fill empty space.

## Consistency across a series

Always reuse the same white background, mint banner, headline sizing, gray border, body color family, connector weight, and icon line weight across cards. Topic changes affect **content/layout**, not random palettes. 1024×1024 output for each card. The eight reference crops have the same 468×468 native dimensions and are not themselves generated output.

## Optional legacy saturated themes (opt-in only)

| Theme | Card background | Board |
|---|---|---|
| mint | `#34EDBE` | `#1FE2B5` |
| sky | `#4DCDED` | `#43BFE8` |
| peach | `#FFA678` | `#FD9361` |
| lavender | `#A2B0FA` | `#93A4F2` |
| lime | `#58DF3D` | `#44D333` |
| pink | `#E58CD3` | `#D979C6` |

Use those themes only on explicit request. Previous saturated-reference thumbnails still exist in `../assets/reference-*.jpg` for that alternative art direction.

## Quality rejection criteria

- Inconsistent card dimensions, title styles, background colors or border thickness within a set.
- Missing, swapped, invented or reversed Mermaid connections; wrong yes/no edge labels.
- Node text outside its shape or too small to read; overly dense, cluttered, decorative arrows.
- Cropped corners, photograph effects, illegible AI-generated text, arbitrary logos.
- Mint title bar missing for the **default** style.
