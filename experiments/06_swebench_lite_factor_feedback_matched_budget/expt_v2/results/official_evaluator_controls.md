# Official evaluator control reconciliation

**TLDR:** The pinned evaluator ran all eight report-backed gold controls and six exact-empty-base adapter controls. Two exact-empty cells are null after their literal-empty and unadmitted marker attempts consumed the available retry allowance; none is silently scored. The controls validate evaluator operation only, not repair improvement.

Raw predictions, reports, logs, test identities, and adapter source remain in evaluator-only storage. This published view intentionally contains only identifiers, statuses, resource totals, and hashes.

- Harness commit: `f7bbbb2ccdf479001d6467c9e34af59e44a840f9`; panel hash: `552c8bde40bc102b2145607e79cdffaeff45ad50e30011cafaf311890a819e7d`.
- Reconciliation manifest: `aed7659c576300c662b4668356b9fd819db50a977c512a8f038e95d4c10bba9e`; adapter source hashes: run-evaluation `51fac8d78ff0ff20cd58eac91f24262a9d475346a51b08da321c87fc6174f9b8`, Docker-limit patch `b323bac996c6cc7ce7d21ec7de3e2f58418cd5b69485fe59b3bbaedbb752519e`.
- Report-backed gold: 8/8; exact-empty adapter: 6/8; aggregate wrapper elapsed seconds: 2275.874; serial driver, max two containers, 4 CPU/8 GiB per container, 1800-second cell timeout.
- The private report audit found 8/8 applied patches, 3 resolved and 5 unresolved gold reports; all reports carried test-status maps, with no collection/import/timeout marker in the reported failure lists. This does not eliminate unobserved environment causes, so unresolved controls are not used as semantic evidence.
- The 4 CPU/8 GiB container limits and per-test timeout were enforced and observed. The outer process did not enforce a separate build-time timeout or 120-GiB new-storage ceiling, and elapsed×4 is an allocation estimate rather than measured CPU use; those limitations remain attached to every count.

| Task | Gold | Exact empty baseline | Published receipt/report hashes |
|---|---|---|---|
| `sqlfluff__sqlfluff-1763` | resolved | NULL — retry allowance consumed by preserved filtered/marker attempts | receipt `f45420b776b5fbcf` / report `76faa77afa5effcd` |
| `pvlib__pvlib-python-1606` | unresolved | NULL — retry allowance consumed by preserved filtered/marker attempts | receipt `514dcb1c2d4a5d02` / report `3fa72842b931e33d` |
| `sqlfluff__sqlfluff-2419` | resolved | unresolved | receipt `e665ecf2833177ee` / report `377853a4a319cc54`; receipt `f98c73acde274bc7` / report `be0b6be385518236` |
| `marshmallow-code__marshmallow-1343` | resolved | unresolved | receipt `e6e304fe640717f3` / report `b475dee94fb8b2f3`; receipt `998bd3c25fc72bbc` / report `394708f5bdfd6486` |
| `pvlib__pvlib-python-1707` | unresolved | unresolved | receipt `84484b5862066674` / report `c62e83147a9107bb`; receipt `dc5e695c748743a9` / report `c62e83147a9107bb` |
| `pvlib__pvlib-python-1154` | unresolved | unresolved | receipt `e9cdc2458225cca3` / report `82bf8021e9dc799e`; receipt `fb5e9066c787e0ae` / report `82bf8021e9dc799e` |
| `pvlib__pvlib-python-1072` | unresolved | unresolved | receipt `63b6b0d6839eff4a` / report `7fab79f6592f3a5c`; receipt `fc3182c1545c3100` / report `7fab79f6592f3a5c` |
| `pydicom__pydicom-1139` | unresolved | unresolved | receipt `aa279101ecec2c2d` / report `c9b2aca9a123f4a2`; receipt `4626c33eaf0dd73b` / report `9367d8dbe2e014d1` |

The original literal-empty wrappers exited zero because the upstream harness filtered empty predictions before test execution. They are retained as unmeasured infrastructure receipts. The marker-file variants for `sqlfluff__sqlfluff-1763` and `pvlib__pvlib-python-1606` executed but changed the base tree, so they are retained only as unadmitted attempts and are excluded from all counts above.
