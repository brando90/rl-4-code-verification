# Experiment 25, expt_v2 (R5 generator and Q1), checkpoint 10-28-2026 15:30 PT
- Generator (completion.py, build_items.py, gen_vllm.py, score_measure.py) and tests/test_e25_completion.py are written.
- 0e smoke PASSED on skampere1 GPU 5 (delphi-1e21-3.4B, bf16): results/0e_smoke_delphi_3p4b.json.
- Q1 3.4B (base, seed42, seed62746) generated and scored: results/q1_3p4b_*_measure.json. 9.7B base generated (raw files in scratch/at1789/q1_9p7b_base, not yet scored); 9.7B seed42 downloaded on skampere1 (~/e25/hf), not generated; 9.7B seed62746 not downloaded.
- skampere1 download note: set HF_HUB_DISABLE_XET=1 (xet stalls). Run each step under 280 s (ssh_run limit); items in ~/e25/items, gen_vllm.py in ~/e25.
- Still to do: 9.7B seed42 and seed62746, score all, P6 verdict, Q3 (P8) on CPU, README fixes, results.md rewrite, delete my downloads in ~/e25/hf on skampere1, push, comments.
