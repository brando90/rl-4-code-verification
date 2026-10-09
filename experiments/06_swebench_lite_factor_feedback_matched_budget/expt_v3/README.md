# Version 3: validate environments before factor-feedback repair

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v3/README.md>

**TLDR:** Brando authorized automatic implementation and execution on 10-08-2026. Validate the unchanged eight-task panel with repaired public dependency environments and strict diagnostic transport, then run the complete matched repair comparison only if the validity gates pass. No version-3 measurement has started.

Created: 10-06-2026. Updated: 10-08-2026. **Status:** IMPLEMENTATION AUTHORIZED; EXECUTABLE FREEZE PENDING.

## Why this version exists

Version 2 produced only 2/8 valid gold/empty control pairs and 1/8 structurally accepted diagnostic bundles, below the separate 6/8 engineering gates. Seven control cells aborted on imports, two have ambiguous fixture failures, and two empty-patch cells exhausted retries. The exact parser also lacked a prospectively frozen implementation hash. Those failures remain in the [official-control audit](../expt_v2/results/official_evaluator_controls.md) and [diagnostic audit](../expt_v2/results/diagnostic_rejection_audit.md); this version never overwrites them.

The research question is whether decomposed public feedback improves independent official issue resolution at a matched repair budget. Raising the public geometric mean alone does not answer it. The three components are execution viability, public regression preservation and public issue-check success. This is a coding diagnostic, distinct from VeriBench's Smooth Conjunctive Score for Code verification (SCSC).

## Current plan and admission

The [new protocol](PROTOCOL.md) is authoritative; the [remote runbook](cc.md) defines execution and recovery. The original 10-06-2026 proposal remains in Git history. The new authorization replaces its former zero allowance, and project decision D-108 requires Vals-funded Valkyrie for every measured response. Personal subscriptions may coordinate, implement and review only.

1. Freeze public dependency environments and an audited empty-patch adapter; run all 16 new official gold/empty controls. At least 6/8 pairs must have valid gold-resolved/empty-unresolved outcomes.
2. Freeze the exact prompt, structured-argument validator, isolated runner, public contexts and client contract. Make one diagnostic-author call per task, at most eight. Invalid responses are retained without salvage or replacement. Structural acceptance and actual base behavior are separate measurements.
3. Require at least six of the same eight tasks to have both valid official controls and usable public diagnostics. If the gate closes, report its measured denominator and retain unused solver allowance.
4. Otherwise freeze and complete all 56 solver cells: eight shared initial patches plus three feedback conditions × two repair responses × eight tasks. Evaluate the eight initial and 24 final patches only after they are immutable; report paired differences, uncertainty, missingness bounds and actual costs.

The eight tasks remain development/validation data whose earlier outcomes were inspected. A later 24-task test confirmation needs a separately frozen version and does not depend on obtaining a positive pilot effect. No test confirmation or training is added implicitly to this version.

## Execution bounds

No graphics processors. Maximum two containers × four processors × eight gibibytes, 160 processor-hours, 18 elapsed hours from admitted remote setup/control execution, and 120 gibibytes each of new owned Docker and scratch data. Preserve 100 gibibytes Docker-root headroom and one tebibyte at the actual scratch filesystem, jointly accounting for shared devices. Enforce build/cell timeouts and exact owned-resource cleanup. At most one identical deterministic infrastructure retry per cell, within the cumulative envelope; no fresh model-response retry.

The original host's Docker socket became inaccessible after its 10-08-2026 reboot. A prospective root-backed private runtime on `skampere2` preserves the same headroom limits; exact host/storage and backend enforcement still require an execution manifest and live verification before controls. No shared data is pruned and no daemon permissions are changed.

## Artifacts

- `PROTOCOL.md`: authorized scientific design, gates and resource envelope.
- `cc.md`: self-contained remote execution and recovery instructions.
- `diagnostic_author_prompt.txt`: bare structured-response transport contract.
- `scripts/diagnostic_validator.py`: deterministic structural acceptance and hashes.
- `scripts/diagnostic_runner.py`: disposable public-only container execution and typed receipts.
- `scripts/control_runner.py`: complete control declaration, durable budgets, identity checks and backend observations; actual backend enforcement must be established separately.
- `scripts/test_*.py`: synthetic deterministic checks; no model or real Docker calls.
- `../results.md`: live status, with historical results kept separate.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Version 3 is authorized and being implemented; measured execution follows the executable freeze, verified funding/resource limits and unchanged validity gates.
