---
name: debug-workflow
description: Entry point for a new bug report or incident symptom. Runs locate-system-problem to file a BUG record, then reads that record to decide whether deep-investigate-system-bug is needed. Use this instead of calling either skill directly, unless the maintainer names one.
---

# Debug workflow

Take a symptom to a filed bug record, and go deeper only when the record leaves
the cause unproven. This skill orders the steps and makes the depth decision.
The leaf skills own the method; do not restate their rules here.

## Input expected

A symptom from the maintainer and any clues they have: a run ID, log line,
timestamp, service name, or an existing `BUG-NNN`.

## Steps

1. **Style.** Load
   [writing-clearly-and-concisely](../writing-clearly-and-concisely/SKILL.md).
   Apply it to the bug record, the investigation, and the final report.
2. **Locate.** Run [locate-system-problem](../locate-system-problem/SKILL.md).
   Its output is `<service>/docs/testing-docs/bugs/BUG-NNN-<slug>.md`. If the
   maintainer supplied an existing `BUG-NNN`, skip this step and use that
   record.
3. **Decide depth.** Read the bug record from step 2 and apply the gate below.
   Decide from what the record proves, not from how serious the impact is.
4. **Investigate, if deep.** Run
   [deep-investigate-system-bug](../deep-investigate-system-bug/SKILL.md) with
   the record from step 2. Its output is `BUG-NNN-investigation.md` next to the
   record.
5. **Report** in the format below.

Do not implement a fix unless the maintainer asked for one.

## Depth gate

The bug is **shallow** when the record shows all of these:

- One code or configuration path, cited by `file:line`, is **Proven** to cause
  the symptom.
- The steps to reproduce trigger the original failure, not only its outcome.
- No edge on the causal path is still a **Hypothesis** or an **Unrun probe**.
- The cause and the failure that the maintainer saw are in the same component.

The bug is **deep** when the record shows any of these:

- A causal edge is still a **Hypothesis** or an **Unrun probe**.
- The trigger is transient, intermittent, timing-dependent, or not reproduced.
- The component that reported the error is not the one that started it, or
  the failure crosses a process or service boundary.
- Two causes act together: one starts the failure and another makes a
  recoverable failure terminal.
- An upstream library is implicated and its installed behavior is unverified.

When a record meets neither list cleanly, treat it as deep.

Examples from `etl-poc`:

- [BUG-012](../../../etl-poc/docs/testing-docs/bugs/BUG-012-website-crawl-fails-on-dead-image-host.md)
  is shallow. Every causal edge is Proven with `file:line`, each competing
  cause is rejected, and the same partition fails the same way on every run.
- [BUG-014](../../../etl-poc/docs/testing-docs/bugs/BUG-014-transient-code-location-error-fails-asset-backfill.md)
  is deep. The malformed gRPC response did not reproduce, and an unset daemon
  guard turned that transient error into a failed backfill.

## Output

End with this report:

```markdown
- **Bug:** BUG-NNN — <summary line from the record> ([record](<path>))
- **Depth:** Shallow | Deep — <the gate condition that decided it>
- **Cause:** <proven cause with file:line>, or <the question still open>
- **Open:** <hypotheses and unrun probes>, or None
- **Next:** <cheapest next probe>, or <fix to consider>
- **Files:** <records and evidence files created or changed>
```

Keep each line to one or two sentences. Put detail in the bug record or the
investigation, and link to it.
