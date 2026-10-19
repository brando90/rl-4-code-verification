# Generation dependency repair and startup recovery

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/AMENDMENT_generation_environment.md

**TLDR:** Two control-generation startup attempts failed before producing any benchmark outputs. Repair only eth127's dependency fallback, retain both failures, then make one additional identical startup attempt after full model-class inspection passes. Both trained checkpoints, all validation prompts and all sampling settings remain unchanged.

On 10-19-2026, the standalone generation interpreter inherited incompatible operating-system packages: SciPy expected NumPy below 1.28, while the frozen generation environment contains NumPy 2.3.5. After fixing SciPy, the first retry exposed an old PyOpenSSL package incompatible with the generation environment's cryptography 50.0.2. These were import failures, with zero generated cells and no loaded-model inference.

The owned LFS directory `python_user/lib/python3.12/site-packages` supplies SciPy 1.16.2 and PyOpenSSL 26.4.0. The previously absent `~/.local` points to this owned directory; shared environments are untouched. An intermediate PyOpenSSL 25.3.0 installation failed a CPU-only import check and was upgraded before any successful generation. Full Qwen3 model import and vLLM's separate-process model inspection now pass. Torch 2.13.0, Transformers 5.18.0, vLLM 0.30.0, model files and sampling arguments are unchanged.

This prospectively permits one additional startup attempt beyond the original single infrastructure retry, after the full inspection passes. Preserve the first retry's receipt/log under `primary_recovery/attempt_1`, then execute the exact same generation command. No existing generated cell is resampled or discarded; all 1,080 cells for this condition remain required. There is no automatic retry loop. Later failure remains visible for diagnosis.

The recovery uses GPU 1 with existing allocator gates. Its CPU scoring waits for the original supervisor's scoring to end. The 4B successor then waits for this recovery's scoring to finish, retaining the maximum of eight simultaneous scoring jobs. The original supervisor's recorded generation failure is reconciled only after the identical retry and all eight scoring jobs succeed.
