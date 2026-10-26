# Three-run failure breakdown

**Doc link:** [classification evidence](results/classified_summary.json); [future logging](future_logging/README.md)

**TLDR:** All3,240 validation outputs are accounted for. Fresh models no longer emit the earlier broad proof-search tactics, but still fail on unknown names, types, explicit proof steps and decision procedures. Future scoring now retains raw compiler/kernel logs.

## Complete breakdown

Each column contains1,080 outputs. Every output appears once, classified by its first recovered compiler diagnostic, or its official success/extraction status. These are observed error symptoms, not independently established causal root causes.

| Outcome / first diagnostic | Earlier11.11% | Fresh1.85% | Fresh+500tiny1.57% |
|---|---:|---:|---:|
| Success | 120 | 20 | 17 |
| No extracted Lean (all length-capped) | 109 | 130 | 166 |
| Unknown name, tactic or member | 86 | 183 | 138 |
| Failed proof search (simp/omega/etc.) | 53 | 0 | 0 |
| Failed decide/native_decide procedure | 15 | 42 | 26 |
| Decision procedure reports proposition false | 195 | 159 | 187 |
| Other failed proof step / unsolved goals | 152 | 85 | 82 |
| Type mismatch | 151 | 173 | 197 |
| Instance/type inference failure | 70 | 60 | 52 |
| Syntax/notation error | 62 | 112 | 98 |
| Other error / no formatted error | 51 | 80 | 90 |
| Diagnostic timed out; no first error recovered | 16 | 36 | 27 |

The last column also adds125 existing explicit Workbook alternatives. The earlier run continued an already fine-tuned checkpoint; both fresh runs began from original pretrained weights. They are different training setups.

## What the automation counts mean

- Explicit simp/omega/etc. failure diagnostics occurred somewhere in314 earlier-run outputs, and zero outputs in either fresh run. The table uses only the first diagnostic, hence53 earlier outputs in that primary bucket.
- Failed decide/native_decide procedures plus false-proposition reports were the first error in210 earlier outputs,201 first-fresh outputs and213 tiny-augmented outputs. False-proposition reports may come from concrete tests and may reflect a wrong implementation, statement or test; they do not prove that the tactic itself is faulty.
- The first diagnostic was positioned on a plain decide source line in43/79/59 failed outputs respectively; on a native_decide line in218/176/209. These source-location flags overlap table categories and are not added to the totals.
- Unknown names/members include nonexistent names, namespace mistakes and invalid field references; this does not establish that every instance is an invented theorem.

## Recovery and limits

Reused851 source/hash-checked earlier diagnostics and recovered930+897 missing fresh-run diagnostics with96 parallel single-threaded Lean processes on skampere1. Pinned Lean4.22.0/Lake adapter and original source files were retained. Diagnostic checks had a20-second bound, matching the earlier diagnostic pass; a diagnostic timeout is not an official600/900-second scoring timeout. Scores remain unchanged. All2,678 failure receipts retain stdout/stderr hashes, exact source hash, command, exit and timeout status. Earlier combined logs cannot be separated into their original streams.

Raw protected diagnostic artifacts remain under `/lfs/skampere1/0/eth127/rl4cv_tiny_training/failure_diagnostics_v24/`; classified_summary.json binds the full classified_cells.csv SHA. No held-out task text or errors were supplied to a teacher. No model calls occurred.

## Future-run logging fix

Use [future_logging/parallel_scoring_logged.py](future_logging/parallel_scoring_logged.py) for new run versions25+. The default command factory always invokes the logged scorer and retains stdout/stderr, partial timeout output, source/compiler identities and exit/unknown-exit status for compilation and kernel checks. Durable files survive temporary-probe cleanup and controlled abrupt-stop tests. Frozen verification bytecode, acceptance rules and timeout limits remain unchanged. [Actual core and entry controls](future_logging/results/) passed. The original completed-run scorer/pins were preserved for reproducibility.
