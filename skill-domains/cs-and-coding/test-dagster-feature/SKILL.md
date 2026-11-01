---
name: test-dagster-feature
description: Validate and diagnose additions or changes to Dagster assets, checks, jobs, schedules, sensors, resources, and deployment configuration through a real Dagster control-plane run. Use whenever a Dagster feature is implemented, reviewed, or fails at runtime; unit tests and direct Python execution alone are insufficient.
---

# Test a Dagster feature

A Dagster feature is complete only after it runs through Dagster and its
recorded events prove the expected behavior. Run focused unit tests first, but
do not treat `pytest`, definitions loading, mocks, direct function calls, or an
in-process `dg.materialize` call as the runtime acceptance test.

## Run through Dagster

Identify the repository's active Dagster topology and use its normal webserver,
daemon, code server, instance storage, executor, and resources. Rebuild or reload
the code server when its image copies source code instead of mounting it.

Launch the smallest job that exercises the feature through the Dagster UI,
GraphQL API, or Dagster launch command. Use a safe local or development
partition and explicit run configuration. Do not trigger production schedules,
backfills, sensors, or paid external work unless the user authorized that scope.

Wait for a terminal run status, then inspect Dagster's run and event records.
Verify the evidence relevant to the feature:

- step success or failure events;
- asset materializations and metadata;
- blocking asset-check evaluations;
- partition keys and run configuration;
- sensor or schedule tick results when they are part of the change;
- the external boundary, such as the expected S3 object or database row.

Report the job name, run ID, terminal status, tested partition or configuration,
and the observed materialization or failure evidence.

## Diagnose failures from Dagster records

Start with the failed run stored by the Dagster instance. Read its step failure,
run failure, and error-chain events before reading container logs. Classify the
failure boundary as deployment configuration, Dagster orchestration, resource
initialization, user code, or an external dependency. Trace only the implicated
configuration and code after establishing that boundary.

Check required environment variables by presence without printing their values.
Do not use commands that render a fully interpolated Compose configuration when
it contains secrets. Prefer targeted container inspection, documented variable
names, and redacted output.

Do not retry blindly. Explain the recorded cause, correct it when the task
authorizes a fix, reload the affected service, and launch a fresh Dagster run.
The final verification is another Dagster run with a successful terminal status
and the expected runtime evidence.
