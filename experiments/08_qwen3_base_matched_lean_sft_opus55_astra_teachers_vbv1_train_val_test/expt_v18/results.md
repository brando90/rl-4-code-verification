# V18 results: Complete original-pool explicit proof cleanup

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** User stopped further proof generation and requested immediate training. The immutable available-data snapshot admits800strict sources from1,050kernel-verified at cutoff; all2,585originals are accounted.250verified proofs lack required commentary and remain preserved outside training. V20 received the exact ready hashes.

| Cohort | State | Verified | Conservative charge | Ordinary-rate estimate |
| --- | --- | ---: | ---: | ---: |
| Inherited V13 replacements | 795 admitted; 23 lack inline comments | 818 | Included in prior V13 spend | Included in prior V13 spend |
| Unchanged originals | Current kernel audit passed; 227 lack sketch header | 227 | $0 API | $0 API |
| Mixed-length four-file calibration | Two bounded turns finished | 0/4 | $2.531120 | $1.269566 |
| Shortest-four calibration | User stopped first turn; exact checked proof saved | 1/4 | $0.805925 | $0.420352 |
| Reflexivity prescreen | Stopped; 4 admitted at snapshot cutoff | 4 | $0 API | $0 API |
| Final admitted original pool | Strict commentary, receipt, FILE/token and protected screens passed | 800 | $3.337045 additional V18 | $1.689919 additional V18 |

The first mixed-length sample did not support the prospective additional conservative forecast of $154–$308. Its failures and cost remain recorded. No broad paid rollout occurred. Every admitted file retains the original implementation and specifications and passes the frozen kernel, original FILE/Qwen format,16,384-token cap and764-reference overlap screen (0exact/0near). No automated fallback is admitted. Final available-source breakdown:795inherited Terra+1new Terra+4CPU; source indices are bound in [completion](results/available_completion.json), with all outcomes in [row results](results/row_results.csv) and missing-commentary indices in [missing commentary](results/missing_commentary.csv). These are configured-price estimates, not invoices.

Completion SHA256: `bed044e9789b3fe2bacefef59d7fd2c8d2c3005b4d8403608b29e73a0f18fd9a`. Training SHA256: `bc29f309b387cbf27f9e5e89c5ca66c81137d8a5fe67d617dff5738e6f93f998`. State `USER_STOPPED_PARTIAL` expressly records that remaining repair batches were not all attempted. The CPU prescreen reached925/1536 and found a fifth success after the fixed cutoff; that artifact is preserved but excluded from this immutable800-row pool.
