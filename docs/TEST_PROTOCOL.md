# Test Protocol: Quote Service

This protocol is for anyone changing the quote service. Follow it in order.
It covers what to run, what each test layer proves, how to handle a failure,
and when a change is ready to merge.

## 1. Set up

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12 is the version CI uses.

## 2. Run the suite

```bash
pytest
```

Expected result: all tests pass. The perf line prints median and p95 latency.
Typical values on a laptop are a median near 1 ms and a p95 near 1–2 ms.

## 3. What each layer proves

| Layer | Location | Proves |
|---|---|---|
| Unit | `tests/unit/` | Business rules: validation, totals, rounding, discount range. |
| Integration | `tests/integration/` | HTTP status codes, JSON errors, and body limits over real sockets. |
| Regression | `tests/regression/` | Each fixed bug stays fixed. One test per bug ID. |
| Performance | `tests/perf/` | p95 latency of `POST /quote` is under `PERF_P95_MS` (default 50 ms). |

## 4. When a test fails

1. Read the failure before changing code. Decide whether the code or the
   test is wrong. Changing a test to match new behavior requires a written
   reason in the PR description.
2. If the failure is a real bug, add a regression test first. Name it
   `test_bug_<ID>_<short_description>` and put it in `tests/regression/`.
   Confirm it fails on the broken code, then fix the code, then confirm it passes.
3. If the failure is in the perf test, do not raise the threshold to get past it.
   Find the slowdown first. Raising `PERF_P95_MS` is allowed only when the CI
   runner class changes, and that change must be recorded in the PR.

## 5. Checking the perf gate itself

The gate must be able to fail. To confirm it still does:

```bash
PERF_P95_MS=0.001 pytest tests/perf   # must exit with status 1
```

Run this after any change to the perf test or the HTTP layer.

## 6. Ready-to-merge checklist

- [ ] `pytest` passes locally.
- [ ] Every bug fixed in this change has a regression test with its bug ID.
- [ ] No test was deleted or weakened without a written reason.
- [ ] CI is green, including the perf job.
- [ ] Money values in new responses are exact two-decimal strings (see BUG-102).

## 7. Known limits

- Perf numbers depend on the machine. The 50 ms threshold is set for
  shared CI runners and is loose enough to avoid flakiness, but it will not
  catch a 10% regression. Trend data would be needed for that.
- The HTTP server is single-process `http.server`, which is fine for tests and
  not for production traffic.
