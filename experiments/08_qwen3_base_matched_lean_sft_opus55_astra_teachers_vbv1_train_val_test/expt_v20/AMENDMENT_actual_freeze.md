# V20 actual data freeze and device admission

**Doc link:** [prospective protocol](PROTOCOL.md)

**TLDR:** Production started from original Qwen3-1.7B-Base on physical A100 GPU0 with3,568 accepted rows, fresh optimizer and frozen training settings. This record describes actual admission and subsequent discoveries; it does not alter the running cohort or rewrite the frozen protocol.

## Actual freeze

-3,568 rows:684 Python-to-Lean originals,2,145 Workbook exercises,61 Workbook repairs and678 public exercises. Assistant loss tokens2,948,296; one pass means1,784 optimizer updates. Longest combined example8,967tokens.
- Dataset SHA256 `0882a88925e862b44fd79b7592d8d525829aec1f2ac1bd12afa1fd43fc6a5de7`.
- The V18 available pool contains800 rows under its existing admission policy; V20's final full-file/test-proof policy excluded116 more. The exact per-row decisions remain in `results/` and the remote admission manifest; those116 did not enter production.
- After freezing, the inventory owner found125 additional existing explicit Workbook alternatives that earlier global deduplication had omitted in favor of automated proofs. They were discovered after the production cohort froze and are not silently inserted into this run.

## Actual base and hardware

- Official Qwen3-1.7B-Base revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`; model.safetensors SHA256 `6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841`. Configuration/tokenizer files are bound by the initial manifest; frozen training template/vocabulary agreement passed.
- GPU1 became occupied by a foreign process before admission. The dispatcher instead selected empty GPU0 after shared lease/device checks. No foreign process was interrupted. CUDA visibility is fixed to this one device.
- Base-specific discarded longest-plus-shortest control passed, then production reloaded original weights with a fresh optimizer. Actual production first update occurred at Unix1792436728 under PID614959. No prior SFT weights or optimizer state were loaded.
- Root independently observed57updates/89,414loss tokens and later97updates/155,058tokens with status RUNNING. These are progress observations, not final results. Live receipts supersede these snapshots.

## Newly authorized tiny repairs

User subsequently requested25 Terra workers to repair the500 tiny examples. That is a separate V21 corpus with independent checked outputs. It does not mutate the running V20 training dataset. Further training on those repairs requires a separately recorded regime.
