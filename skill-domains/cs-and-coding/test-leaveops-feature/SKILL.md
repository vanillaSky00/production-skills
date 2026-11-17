---
name: test-dagster-feature
description: Validate LeaveOps features through FastAPI calls, related Temporal workers, PostgreSQL and MinIO effects, and exception handling. Use when testing or diagnosing an endpoint or its background processing, persistence, or deployment changes. Report failures, retries, swallowed exceptions, and unverified checks explicitly.
---

# Test a LeaveOps feature through FastAPI

The skill name is retained for existing invocations. LeaveOps currently uses
FastAPI and Temporal; a Dagster run is not an acceptance requirement.

Verify the feature at its real entry point and follow its effects through every
related boundary. For an endpoint, that means an HTTP request, the related worker
when applicable, and persisted results. A 2xx response, `/healthz`, passing unit
tests, mocks, or direct route/activity calls alone do not prove that flow works.
Never hide a failure or describe an unverified boundary as passing.

## Establish the feature's path

Read the changed code, its callers, and relevant tests. Identify the expected
behavior and the boundaries the feature actually uses:

- HTTP method/path, path and query parameters, JSON or multipart fields, request
  validation, response schema, status codes, and exception handlers.
- Database writes or queued events, dispatcher, Temporal workflow/activity,
  namespace/task queue, retry policy, and expected state transitions.
- PostgreSQL rows/constraints/transactions and MinIO objects, plus Hermes/model
  calls when the feature invokes review.

Start from `leaveops/src/api/`, `leaveops/src/models/`,
`leaveops/src/orchestrator/`, `leaveops/src/io/`, and
`leaveops/src/exceptions/`. Use `leaveops/tests/` for existing fixtures and checks.
Consult `docs/developer-onboarding-docs/use-api.md`,
`docs/developer-onboarding-docs/deploy-locally.md`, and
`deploy/compose/compose.yml` for the runtime and calling conventions. Confirm
contracts against current routes/schemas and the running API's `/openapi.json`;
report disagreements instead of silently choosing the easier expectation.

For a feature with no endpoint, exercise its normal worker, schedule, or service
entry point and verify its effects. Mark unrelated boundaries not applicable
with a reason; do not invent an endpoint or require a worker for a read-only API.

## Prepare and run focused checks

Use the normal local/development API, worker, PostgreSQL, MinIO, and Temporal
services required by the feature. Confirm the target and running code version;
rebuild/recreate affected services when source is copied into an image. Check
worker workflow and activity pollers, using `scripts/testing/check_worker.py`
inside the worker where appropriate. `/healthz` checks the API, PostgreSQL, and
MinIO; it does not establish worker, Temporal, or model readiness.

Run the relevant existing tests first, from `leaveops/`, using the project's Python
environment and `python -m pytest <relevant paths> -ra --tb=short`. Integration
tests require `RUN_INTEGRATION=1` and configured services; Temporal-marked tests
need a Temporal test server. Inspect collection and skip results. Report missing
dependencies, skipped tests, and unavailable services as verification gaps.

Use synthetic data with unique external IDs and keep returned IDs for tracing.
Do not trigger production schedules, real leave decisions, or paid external work
without authorization. Inject dependency failures only in isolated tests or a
dedicated local environment, not by disrupting shared services. Test cleanup must
be limited to the test's own records, objects, and workflows.

## Verify endpoint calls over HTTP

Call the running FastAPI app through HTTP with the actual request encoding and
field names. Cover the happy path and relevant rejection cases: malformed or
missing fields, invalid identifiers, missing resources, wrong request state, and
duplicates. Assert exact status codes and meaningful response fields, not just
that the call returned. Include filtering, limits, or file validation when they
belong to the changed contract.

Current calling details to verify when relevant:

- `POST /ingest` uses multipart `manifest` and repeated `files[]` fields. A new
  manifest returns 201; replaying the same manifest returns 200 with the original
  batch. Use a fresh `external_id` for a new processing test. An empty `accepted`
  list does not prove that a new request reached the worker.
- `GET /batches/{batch_id}` and `GET /leave-requests/{leave_id}` must return the
  correct related records; compare their values with persisted data.
- `POST /leave-requests/{leave_id}/supplements` uses multipart `files[]` and
  requires `needs_supplement`. `POST /leave-requests/{leave_id}/decision` uses the
  `HumanDecision` JSON schema and requires `needs_human`. Check returned
  `event_id`, 409 conflicts, and prevention of duplicate submissions.
- Check 404 for well-formed unknown IDs and 422 for request validation failures,
  including the registered `BatchError` handler's `detail` payload.

Capture the HTTP status and response body even for expected errors. Use bounded
requests and tools that preserve failures, such as curl with `--fail-with-body
--silent --show-error --max-time <seconds>` plus status capture. Do not suppress
stderr, discard error bodies, or use `|| true` to make a failed check look green.

## Follow the related worker and stored effects

For asynchronous features, retain the batch/request/event IDs and correlate them
with the Temporal workflow ID, run ID, activity attempts, and worker logs. In the
current flow, ingestion persists `received` requests; scheduled dispatch starts
`leave-{leave_id}` workflows. Supplement/decision endpoints persist events for
later dispatch. HTTP success confirms submission, not worker completion.

Poll with an explicit deadline appropriate to dispatch, inference, and retry
settings. Verify the feature's expected terminal state or deliberate waiting
state, using Temporal history/query results and a fresh database session:

- Check that the correct workflow/activity consumed the intended input and
  attachment/event IDs. Inspect retry counts and failure chains as well as the
  final workflow result.
- Query the exact related PostgreSQL rows. Verify status transitions, review
  rounds, audit records, foreign-key relationships, and timestamps. Terminal
  requests must have `completed_at`; waiting states must not be called completed.
- For events, verify `pending` becomes `delivered` or an explicit `rejected`
  outcome with error evidence. Confirm the resulting workflow and request state;
  delivery alone does not prove the business operation succeeded.
- For attachments, verify referenced MinIO objects exist and match stored
  metadata/content. Check rollback, deduplication, and idempotency where changed:
  no unintended committed rows, duplicate events/reviews/workflows, or unexplained
  leftover objects after a rejection or failure.

Do not force database states or call activities directly to manufacture runtime
success. Isolated fixtures may set up a state for a focused test; disclose that
setup and verify natural transitions separately. If the deadline expires, report
the last state, pending work, and available error evidence as incomplete or failed.

## Verify exceptions and make failures visible

Exercise relevant validation, conflict, dependency, and worker failure paths.
Isolated fault injection can prove handling, but label simulated failures and
keep them distinct from evidence collected through the running stack.

- Verify expected exception types reach the intended handler and produce the
  documented status/body. Unexpected database, storage, Temporal, or model errors
  must not become success responses, empty results, or misleading client errors.
- Verify transaction rollback and resulting worker retry, rejection, or fallback
  behavior. Preserve the cause and traceback in appropriate logs/history/audit
  records without exposing internal errors or secrets to API callers.
- Inspect broad catches, `except: pass`, log-only catches, default/empty returns,
  startup retry loops, and retry exhaustion. Report any lost error evidence. A
  narrow handler for an expected idempotency conflict is acceptable when its
  outcome is verified; it must not absorb unrelated exceptions.
- Inspect `review_attempts.status/error/responses`, `events.status/error`, Temporal
  activity failures, and API/worker logs as relevant. A workflow can continue to
  `needs_human` after review errors. Distinguish this from a valid `undecidable`
  review: report the underlying failure even if a later human decision completes
  the workflow. The default unconfigured organization rules can legitimately
  yield `undecidable`; do not assume every successful review must approve.

Tell the user promptly about unexpected failures, recovered errors/retries,
swallowed exceptions, and blocked checks. A negative test can pass by observing
its expected error; an unexpected error cannot be erased by a later successful
retry. Keep it in the report with the eventual outcome.

Diagnose the earliest failing boundary using the HTTP result, persisted audit
records, Temporal failure chain, and correlated logs. Check environment variable
presence without printing values; avoid fully interpolated Compose output with
secrets. Redact credentials and personal data while retaining useful error types,
messages, and IDs. Fix only within the authorized task, reload affected services,
and rerun the failed scenario plus its happy path. Do not retry blindly.

## Report the result

Give a concise result for each applicable boundary: API call, worker/workflow,
database/storage, and exception handling. Use `PASS`, `FAIL`, `BLOCKED`, or
`NOT RUN`; explain any boundary marked not applicable. Include:

- Tested method/path and payload/fixture, expected versus observed status/result,
  and the environment/code version.
- Request/event IDs, Temporal workflow/run IDs, observed state and persistence
  evidence, and relevant test counts including skips.
- Every observed error, retry, fallback, or swallowed exception, its cause or
  remaining uncertainty, and the result after any fix.
- Exactly what could not be verified and what is needed to finish it.

Claim end-to-end success only when all applicable runtime boundaries are
verified. Passing focused or simulated tests while runtime checks are blocked
is partial verification and must be described that way.
