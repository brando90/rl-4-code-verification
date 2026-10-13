# Attempt 2: distinguish information messages from raw streams

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/R0_attempt_2/JUSTIFICATION_streams.md>

**TLDR:** Assert the original `#eval IO.eprintln` marker as an information message, and separately exercise both raw process streams.

Pinned Lean source `Lean/Elab/BuiltinEvalCommand.lean:211` calls `IO.FS.withIsolatedStreams` using `Core.stderrAsMessages`. Attempt 1 retained the original marker in its information message, so requiring raw stderr there was incorrect. The marker, strict 1, proved theorem fraction 1/1 and implementation/example status 1 remain.

Add a scoped `set_option stderrAsMessages false in #eval IO.eprintln` command with a separate marker: the independently expected clean-command count consequently becomes 4/4, with no extra theorem. This tests real per-command raw stderr without changing other source options. The probe also has a `--capture-control` mode that writes unique markers using `IO.println` and `IO.eprintln` outside elaboration; the harness must capture exact stdout and stderr separately, with exit 0, and retain their complete bytes. This control is separate from the fixture measurement and never changes the historical oracle. All expectations are committed before attempt 2.
