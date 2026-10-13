# Attempt 2: real long-message fixture

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/R0_attempt_2/JUSTIFICATION_long_message.md>

**TLDR:** Replace the nonexistent `String.ofList` constructor with an explicit 5,000-character string literal passed to `IO.println`. Preserve the original two output commands surrounding a failed theorem.

Amendment A1 authorizes this correction before attempt 2. Attempt 1's source and failed result remain unchanged. The attempt-1 compiler evidence records two `unknown constant` errors; they are fixture defects, not the intended log-length test. A literal string avoids any version-dependent construction API. The expected historical strict value stays 0, clean commands stay 4/5, implementation/examples stay 1, and proved theorems stay 1/2.

Acceptance will independently require two information messages of at least 5,000 characters, an error attached to the intervening theorem command, the correct 4/5 command fraction and 1/2 theorem fraction, and retention of the whole log. This is a stronger assertion of the originally required property, not an expectation fitted to observed factors.
