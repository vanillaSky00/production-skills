---
name: write-pr
description: Draft or revise a concise LeaveOps PR title and description from the actual diff and relevant eval results. Use when preparing a PR for the team's review.
---

# Write a LeaveOps PR

Keep PRs easy to review for a small team. An issue is not required for each change.

Use [writing-clearly-and-concisely](../writing-clearly-and-concisely/SKILL.md)
when writing the title and description: use active voice, concrete wording,
and only the detail a reviewer needs.

## Write the draft
- Start the Description with a tag on its own line: `two-way door` if reverting
  the PR fully restores the previous behavior and data, or `one-way door` if it
  can't be cleanly undone (data deletion or migration, schema changes, published
  APIs or contracts, external side effects). Write only the tag, with no
  explanation after it.
- Read the intended diff against the PR's base branch; exclude unrelated local edits.
- Write an imperative title under 70 characters describing the change's effect.
  Plain titles and existing `fix(...)` / `docs(...)` prefixes are both acceptable.
- Explain what changes and why in one or two sentences. List only changes that
  help the reviewer understand the behavior or a meaningful tradeoff.
- Use How to Test only for a relevant eval when the changed behavior needs it.
  Give the existing eval command, representative inputs, and observable expected
  results. Include recorded outcomes only when that eval actually ran.
- Do not list pytest, Ruff, formatting checks, or AI-written unit-test pass counts
  as PR testing instructions or evidence that the feature works. Use real eval
  results and inspection of the returned decisions and evidence instead.
- If no eval is needed, write `Not needed — <reason>`. Do not invent an eval
  just to fill the section. If an eval is needed but unrun, write `Not run` and
  give the eval steps. Link the existing eval guide when setup details are needed.
- Check only verified checklist items. Link an existing issue or bug record when
  relevant; do not create one just to fill the PR. Include screenshots only for
  visible changes when useful.

Use the template below, replacing its instructions with facts. Omit Related
Issues and Screenshots when they do not apply. For a tiny change, keep each
section to a sentence or short list. End agent-drafted PR bodies with
`Generated-by: Codex`; do not claim human review that did not occur.

Return the title and body. Publish or update a remote PR only when requested,
using any authorization already given. Preserve Markdown newlines when posting.

## PR titles

Use an imperative title under 70 characters that names the change's effect.
Keep issue and PR numbers in the body rather than the title.

- Good: `Route uncertain leave requests to human review`
- Good: `Exclude human-review cases from decision accuracy`
- Good: `fix(deploy): preserve Hermes config ownership`
- Too vague: `Update ReviewOutput and metrics.py`

## Template

```markdown
## Description

`two-way door` or `one-way door`

What changed and why.

## Type of Change

- [ ] New feature
- [ ] Bug fix
- [ ] Refactoring (no functional changes)
- [ ] Documentation update
- [ ] Infrastructure / CI/CD
- [ ] Performance improvement

## Changes Made

- Specific change and its effect.

## How to Test

Relevant eval steps and expected results, or `Not needed — <reason>`.
State `Not run` when the required eval has not been executed.

## Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-reviewed the code for obvious errors
- [ ] Added or updated eval coverage where needed
- [ ] Relevant eval completed, or no eval needed with a reason
- [ ] Updated documentation if needed
- [ ] No new warnings or console errors introduced

## Related Issues

Link an existing issue or bug record, if relevant.

## Screenshots

Include only when useful for a visible change.
```
