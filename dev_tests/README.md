# dev_tests/

These are **developer-only** tests that exercise the deterministic
(non-LLM) parts of the agent without needing an API key.

They are NOT part of the agent flow. They exist to prove that the
scheduling math (conflict detection, ranking) is correct in isolation,
which is what we need to be confident about for the demo.

## Files

- `edge_case_qdb_collision.py` - asks the scheduler for a Monday
  afternoon meeting and asserts that QDB weekly (Mon 14:00 Doha)
  is correctly detected as a conflict and avoided in the top picks.

## How to run

```bash
# from the project root
python dev_tests/edge_case_qdb_collision.py
```

Exits 0 on pass, 1 on fail.
