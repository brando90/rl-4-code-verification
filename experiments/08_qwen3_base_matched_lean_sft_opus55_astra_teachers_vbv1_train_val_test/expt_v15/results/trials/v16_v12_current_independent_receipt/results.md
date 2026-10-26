# V16 results: Independent ordinary-code receipt recovery

**Status:** COMPLETE on October 19, 2026.

The V6 frozen evaluator recomputed the existing V12-current raw and scored artifacts with `TINY_RUN_ROOT` supplied to the isolated receipt process. It matched the recorded aggregate exactly; this validates the completed measurement but does not change it or establish the 25% target.

| Field | Recorded V12 current | Independently recomputed |
| --- | ---: | ---: |
| Declared cells | 1080 | 1080 |
| Scored cells | 1080 | 1080 |
| Successes | 120 | 120 |
| Success rate | 11.1111% | 11.1111% |

- Validation IDs: 135; raw/scored paths and immutable input hash are in `receipt.json`.
- Returned evaluator vector: 135 task-level rows in `per_cell_recompute.csv`; the inherited raw/scored artifacts retain all 1080 fixed cell records.
- No training, generation, paid model call, GPU use, validation resampling, prompt change, or test-split access occurred.
- The target remains unmet: `120 < 270` successes.
