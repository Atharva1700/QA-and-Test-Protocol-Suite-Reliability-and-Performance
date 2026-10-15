# QA and Test Protocol Suite: Reliability and Performance

A test suite for a small pricing service (`POST /quote`), built to catch
regressions and performance drops in CI, plus a written protocol for anyone
who changes the code.

## What is here

```
src/quote_service/quote.py          Pricing logic (Decimal money, validation)
src/quote_service/http_app.py       stdlib HTTP wrapper around quote()
tests/unit/test_quote.py            Spec tests for the pricing rules
tests/integration/test_http.py      Real-socket HTTP tests
tests/regression/test_regressions.py  One test per bug found (BUG-101, BUG-102)
tests/perf/test_latency.py          p95 latency gate
docs/TEST_PROTOCOL.md               Step-by-step protocol for teammates
.github/workflows/ci.yml            Runs the suite on every push and PR
```

## Run it

```bash
pip install -r requirements.txt
pytest
```

Current result: 37 tests pass. The perf test prints median and p95 latency.

## Bugs found and fixed

The suite was written from the spec before the first implementation was
reviewed. A first draft used float arithmetic and skipped discount checks.
The spec tests exposed two bugs:

- **BUG-101**: `discount_pct` above 100 was accepted and produced negative
  totals. Caught by `test_discount_must_be_between_0_and_100`.
- **BUG-102**: float arithmetic leaked into money fields. The subtotal for
  0.10 + 0.20 came back as `0.30000000000000004`. Caught by
  `test_subtotal_has_no_float_residue_for_simple_prices`.

Both are fixed in `quote.py` (Decimal math, a range check, two-decimal string
output). Each now has a regression test that stays in the suite permanently.

## Verifying the suite itself

Passing tests only mean something if they can fail. Two checks confirm that:

- Running the perf test with `PERF_P95_MS=0.001` exits with status 1.
- The first draft of `quote.py` failed the BUG-101 and BUG-102 tests.

## Design choices

- Tests use only pytest. Integration tests use a real server on a random
  port, not mocks, so the HTTP layer is tested as shipped.
- The perf gate runs in CI with the rest of the suite and fails the job on
  a miss, so latency is treated like any other failing test.
- The protocol doc says what to do when a test fails, so the suite is usable
  by someone who did not write it.
