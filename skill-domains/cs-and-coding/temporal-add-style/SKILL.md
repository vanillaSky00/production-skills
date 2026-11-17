---
name: "temporal-add-style"
description: "Coding rules for adding or editing a Temporal workflow, activity, worker, schedule, or starter in Python (temporalio), so every feature has the same thin layout."
---

# Temporal add style

## 1. Layout: one folder per feature
```
<name_of_schedule>/
  __init__.py
  shared.py        # task queue name + dataclasses
  activities.py
  workflows.py
  worker.py
  schedule.py      # replaces starter.py
```
- Use `schedule.py` when Temporal starts the work on a timer and `starter.py` when it is started on demand. A feature has one or the other.
- One worker per task queue, not per folder. Features that share a queue share one `worker.py` above their folders.

## 2. What each file holds
| File | Holds | Must not hold |
|---|---|---|
| `shared.py` | `TASK_QUEUE`; a dataclass for every input, output and signal | Logic, I/O imports |
| `activities.py` | All I/O, as methods of a class that receives its clients. One activity is one external call or one DB transaction | Client construction, orchestration |
| `workflows.py` | Activity calls, waits, branches | I/O of any kind |
| `worker.py` | Connect, build clients once, register, set `max_concurrent_activities` | Workflow or activity code |
| `schedule.py` / `starter.py` | Create the schedule or start the workflow. Safe to run twice | Anything else |

## 3. Workflow rules
- No I/O, clock, randomness or env reads. Use `workflow.now()` and `workflow.uuid4()`.
- Import activities inside `with workflow.unsafe.imports_passed_through():`.
- Every activity call sets `start_to_close_timeout` and an explicit `RetryPolicy`.
- One dataclass in and one out for workflows, activities, signals and updates. Add fields with defaults; never remove or rename a field.
- Pass IDs and small DTOs, never file bytes, because every argument is stored in history.
- Every wait has a timeout and a defined outcome when it fires.
- A change to the order of activities, timers or waits in a deployed workflow goes behind `workflow.patched()` or into a new workflow type.

```python
result = await workflow.execute_activity_method(
    Activities.fetch_report, request,
    start_to_close_timeout=timedelta(minutes=10),
    retry_policy=RetryPolicy(maximum_interval=timedelta(minutes=5)),
)
try:
    await workflow.wait_condition(lambda: self.approved, timeout=timedelta(days=7))
except asyncio.TimeoutError:
    return Result(status="expired")
```

## 4. Activity rules
- Safe to run twice: use conditional writes, or an idempotency key built from `activity.info().workflow_id` and `activity.info().activity_id`.
- Temporal owns retries: set the HTTP or SDK client's own retries to 0.
- Raise `ApplicationError(..., non_retryable=True)` only when a retry cannot help.
- An activity that can run longer than a minute calls `activity.heartbeat()` and its call sets `heartbeat_timeout`.

## 5. IDs
- A workflow id comes from the business key (`leave-{id}`), never a random value. Start with `WorkflowIDReusePolicy.REJECT_DUPLICATE` and treat `WorkflowAlreadyStartedError` as success.
- A schedule id is fixed. Creating one that already exists is a no-op:

```python
schedule = Schedule(
    action=ScheduleActionStartWorkflow(DispatchWorkflow.run, id="dispatch", task_queue=TASK_QUEUE),
    spec=ScheduleSpec(intervals=[ScheduleIntervalSpec(every=timedelta(minutes=5))]),
)
try:
    await client.create_schedule("dispatch-schedule", schedule)
except ScheduleAlreadyRunningError:
    pass
```

## 6. Size
- 120 lines per file at most; split the feature when a file goes over.
- No base classes, factories, DI containers or generic wrappers until a second real use needs them.

## 7. Tests
- Workflows: `WorkflowEnvironment.start_time_skipping()` with activities mocked by name. Cover each terminal state and each timeout.
- Activities: `ActivityEnvironment().run(...)` against a local fake server.

## 8. Adding a feature
1. Create `<name>/` with the files from section 1, and put `TASK_QUEUE` and the dataclasses in `shared.py`.
2. Write the activities, then the workflow that calls them.
3. Write `schedule.py` or `starter.py` with a fixed id.
4. Register the workflow and activities in that queue's `worker.py`, then add the tests.
