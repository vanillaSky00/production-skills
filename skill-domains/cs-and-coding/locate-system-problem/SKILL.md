---
name: locate-system-problem
description: Trace a system or service problem from a maintainer's short symptom description and partial clues, identify the responsible logic with evidence, and file a reproducible BUG record in that service's docs/testing-docs/bugs directory. Use for repository-backed incident diagnosis; do not use when the request is only to implement an already-known fix.
---

# Locate a system problem

Turn an incomplete incident report into an evidence-backed diagnosis and a bug
record. The maintainer only needs to supply the observed symptom and any clues
they already have; derive commands, paths, and competing hypotheses from the
repository.

## Find the service and its rules

Identify the service named by the maintainer or implicated by the clue. Read
that service's agent instructions, deployment configuration, runtime entrypoints,
tests, operational docs, and recent relevant diffs. Preserve unrelated or
pre-existing worktree changes.

Use the service's `docs/testing-docs/bugs/BUG-000-template.md` as the report
schema. If it is absent, report that gap rather than silently using another
service's template. Choose the next unused `BUG-NNN` number in the service.

## Diagnose from the boundary inward

First establish which process or resource exhibits the symptom. For resource
incidents, collect per-process or per-container evidence before attributing host
CPU, memory, disk, network, or cost to application logic. Then trace that
process through its entrypoint, configuration, persisted state, and user code.

Prefer evidence already available in the repository and read-only runtime
probes. Check version history when it can identify when suspect behavior was
introduced. Compare current worktree code with the checked-in baseline so an
ongoing maintainer change is not mistaken for an established production cause.

Keep these categories explicit:

- **Observed:** supplied by the maintainer or measured directly.
- **Proven:** a code/configuration path and evidence establish the causal link.
- **Hypothesis:** plausible but missing a required measurement.
- **Unrun probe:** an exact command or test that would confirm or reject a
  hypothesis.

Do not turn correlation, a suspicious diff, or an unrun command into a claimed
root cause. If live access is unavailable, locate the narrowest suspect logic,
state the remaining evidentiary gap, and provide probes that discriminate among
the remaining causes.

## Write the bug record

Copy the local template's headings and tables into
`<service>/docs/testing-docs/bugs/BUG-NNN-short-slug.md`. Fill every applicable
field; use `Unknown` or `Not yet measured` where evidence is absent. Preserve
commands and outputs exactly enough for another maintainer to reproduce the
diagnosis. Put large raw artifacts under `bugs/evidence/` and link them.

The report must identify:

- the affected process, host role, environment, and observed impact;
- the smallest responsible code or configuration path supported by evidence;
- competing causes checked and why they were rejected or remain open;
- read-only reproduction and confirmation commands;
- expected versus actual behavior and measured values;
- whether a fix exists. Use `None yet` when diagnosis was requested without an
  implementation.

Add or update a service testing-docs index only when that service already uses
one. Do not invent measurements, claim an unverified fix, mutate production, or
implement a fix unless the maintainer requested those actions.
