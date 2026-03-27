# Testing: baseline checks

Run these for most PRs:

1. `python -m compileall src`
2. `python tests/run_bbox_tests.py`

These checks catch syntax issues and core bbox regressions early.
