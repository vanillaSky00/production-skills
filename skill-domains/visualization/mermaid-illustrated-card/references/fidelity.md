# Mermaid fidelity contract and verification checklist

The Mermaid source defines the graph. Extract a table internally before rendering:

| Field | Required check |
|---|---|
| Diagram kind | `flowchart`, `sequenceDiagram`, `stateDiagram`, etc. |
| Direction / order | TB/LR/BT/RL, or participant lifelines / chronological steps |
| Nodes | Every node ID and exact visible label |
| Shapes | rectangle, diamond/decision, cylinder/storage, double circle, etc. |
| Edges | Exact multiset of (source ID, target ID), including repeated edges |
| Edge types | arrows, no-arrow lines, dotted/dashed lines, bidirectional lines |
| Edge labels | `Yes`, `No`, error, retry, and other annotations on correct edge |
| Groups | subgraph ID/name and each member; preserve nesting where supported |
| Special semantics | loops, join/fork, optional/parallel blocks, activation or states |

## Process

1. Obtain actual Mermaid text, including lines hidden in uploaded Markdown files or attachments.
2. Parse the graph without altering technical terminology.
3. Count nodes and edges before rendering, then compare after rendering.
4. For a JSON spec, preserve original node IDs exactly. Do not invent grouping if Mermaid has none. Preserve all source edges, even if two nodes have multiple different relations.
5. Inspect the rendered card at full resolution and at half scale: node text visible, arrowheads clearly indicate direction, decision branch labels unambiguous, no hidden paths, source shapes recognizable.
6. Resolve problems by changing **layout**, never by deleting relationships. If density exceeds readable one-card capacity, explain this and offer a consistent-size multi-card series rather than silently filtering data.

## JSON diagram contract

The bundled renderer supports a structured graph spec:

```json
{
  "title": "Example System Flow",
  "theme": "mint",
  "direction": "TB",
  "nodes": [
    {"id": "A", "label": "User Request", "icon": "user", "shape": "rounded"},
    {"id": "B", "label": "Authorized?", "icon": "shield", "shape": "diamond"},
    {"id": "C", "label": "Database", "icon": "database", "shape": "database"}
  ],
  "edges": [
    {"from": "A", "to": "B"},
    {"from": "B", "to": "C", "label": "Yes"},
    {"from": "B", "to": "A", "label": "No", "style": "dotted"}
  ],
  "groups": [
    {"id": "Core", "label": "Core Services", "nodes": ["B", "C"]}
  ]
}
```

The renderer supports edge `style` values `solid`, `dotted`, `thick` and flags `undirected` and `bidirectional`. Optional `color` can be applied to a node, but source labels remain unchanged. Prefer the `--mermaid` mode for plain flowcharts, `--spec` mode for a faithful manually inspected complex flowchart, and native Mermaid mode for all other diagram categories.

## Important parser limitation

`scripts/render_card.py --mermaid` is a deliberately minimal, strict parser; it is **not** a full Mermaid grammar implementation. It handles simple flowcharts with inline square/rounded/decision/database labels, branches, labeled arrows, chains, feedback and non-nested subgraphs. It rejects unsupported directives and types with an error. Do not claim successful rendering when parsing fails. For nested subgraphs, dynamic shapes, exotic syntax, sequence diagrams or semantics that cannot be transcribed to nodes/edges, use the native Mermaid engine. All methods need a final visual inspection.
