| Key | Varun | Experiment 08 | Reason |
|---|---|---|---|
| `sft.max_num_steps` | `1024` | `658` | step schedule: ⌈|S| / 2⌉ steps over S in the frozen order (PROTOCOL § 8); per-segment overrides stop at each checkpoint step |
| `sft.val_period` | `256` | `0` | SFT-time validation off (PROTOCOL § 8); the § 9 ladder selects checkpoints |
| `sft.val_batches` | `128` | `0` | SFT-time validation off |
| `sft.val_at_start` | `True` | `False` | SFT-time validation off |
| `checkpointing.checkpoint_dir` | `${oc.env:PHASE1C_CHECKPOINT_DIR}` | `${oc.env:E08_CHECKPOINT_DIR}` | run-specific output directory |
| `checkpointing.metric_name` | `val:val_loss` | `None` | no validation metric; checkpoints are kept by step, never by score |
| `checkpointing.keep_top_k` | `4` | `None` | keep every token-fraction checkpoint |
| `checkpointing.save_period` | `256` | `1000000` | checkpoints at the precomputed token-fraction steps: each training segment ends (is_last_step) at one of them and the next segment resumes from it |
| `policy.model_name` | `${oc.env:PHASE1C_MODEL_PATH}` | `${oc.env:E08_MODEL_PATH}` | run-specific input: the pinned Base snapshot for this size |
| `policy.scheduler` | `[{'name': 'torch.optim.lr_scheduler.LinearLR', 'kwargs': {'start_factor': 0.03225806451612903, 'end_factor': 1.0, 'total_iters': 31}}, {'name': 'torch.optim.lr_scheduler.CosineAnnealingLR', 'kwargs': {'T_max': 993, 'eta_min': 0.0}}, {'milestones': [31]}]` | `[{'name': 'torch.optim.lr_scheduler.LinearLR', 'kwargs': {'start_factor': 0.05, 'end_factor': 1.0, 'total_iters': 20}}, {'name': 'torch.optim.lr_scheduler.CosineAnnealingLR', 'kwargs': {'T_max': 638, 'eta_min': 0.0}}, {'milestones': [20]}]` | Varun's schedule form with W = ⌈0.03 × 658⌉ = 20 warmup updates then cosine over 638 |
| `data.dataset_name` | `ResponseDataset` | `openai_format` | dataset adapter: system + user + assistant messages (Varun's ResponseDataset has no system message) |
| `data.train_data_path` | `/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1/matched_sft_train.jsonl` | `${oc.env:E08_TRAIN_JSONL}` | run-specific input: S in NeMo RL openai_format (host only) |
| `data.val_data_path` | `/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1/matched_sft_validation.jsonl` | `${oc.env:E08_VAL_JSONL}` | loader requirement only: a 2-example file never evaluated (val_period 0, val_at_start false) |
| `data.chat_key` | `<absent>` | `messages` | openai_format adapter key |
| `data.system_key` | `<absent>` | `None` | openai_format adapter: the system message is inside messages |
| `data.system_prompt` | `<absent>` | `None` | openai_format adapter |
| `data.tool_key` | `<absent>` | `None` | openai_format adapter: no tools |
| `data.use_preserving_dataset` | `<absent>` | `False` | openai_format adapter |
| `data.add_generation_prompt` | `False` | `True` | rendering/mask (declared difference): the generation prompt `<|im_start|>assistant\n` belongs to the prompt (no loss), so the loss span is exactly what the policy generates at evaluation (PROTOCOL § 7) |
| `data.input_key` | `input` | `<removed>` | ResponseDataset-only key |
| `data.output_key` | `output` | `<removed>` | ResponseDataset-only key |
| `logger.log_dir` | `${oc.env:PHASE1C_LOG_DIR}` | `${oc.env:E08_LOG_DIR}` | run-specific output directory |
| `logger.wandb_enabled` | `True` | `False` | Weights & Biases off (PROTOCOL § 8) |
| `logger.tensorboard.log_dir` | `${oc.env:PHASE1C_TENSORBOARD_DIR}` | `${oc.env:E08_TENSORBOARD_DIR}` | run-specific output directory |
| `logger.wandb` | `{'project': 'paper1-phase1c-sft', 'name': '${oc.env:PHASE1C_RUN_NAME}'}` | `{'project': 'rl4cv-e08-sft', 'name': '${oc.env:E08_RUN_NAME}'}` | run name (W&B disabled) |
| `logger.mlflow` | `{'experiment_name': 'paper1-phase1c-sft', 'run_name': '${oc.env:PHASE1C_RUN_NAME}'}` | `{'experiment_name': 'rl4cv-e08-sft', 'run_name': '${oc.env:E08_RUN_NAME}'}` | run name (MLflow disabled) |

Per-size differences are only `policy.dtensor_cfg.tensor_parallel_size`, `policy.make_sequence_length_divisible_by` and `cluster.gpus_per_node` (GPU layout): 1.7B: 1 GPU(s), TP 1; 4B: 2 GPU(s), TP 2; 8B: 4 GPU(s), TP 4; 14B: 8 GPU(s), TP 8.

Unchanged in every size (98 keys): optimizer (AdamW lr 2e-5, betas 0.9/0.98, eps 1e-5, weight decay 0.1), max_grad_norm 1.0, global batch 2, micro-batch 1, max sequence length 16,384, bf16, no sequence packing, no dynamic batching, activation checkpointing, seed 20260830, one epoch, shuffle off, add_bos / add_eos on.
