"""CPU stand-ins for tests and the fake-model dry run: a byte-level tokenizer and a tiny randomly initialised Qwen3 (real transformers code path)."""

from __future__ import annotations

from types import SimpleNamespace

import torch

PAD, EOS = 256, 257
VOCAB = 264


class ByteTok:
    """Byte-level tokenizer with the few methods train.py/eval.py use. eos id 257, pad id 256."""

    eos_token_id = EOS
    pad_token_id = PAD
    padding_side = "left"

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=False, **_):
        text = "".join(f"<{m['role']}>{m['content']}\n" for m in messages)
        if add_generation_prompt:
            text += "<assistant>" + ("" if enable_thinking else "<think></think>")
        return text

    def __call__(self, text, add_special_tokens=False, **_):
        return SimpleNamespace(input_ids=list(text.encode("utf-8")))

    def decode(self, ids, skip_special_tokens=True, **_):
        b = bytes(int(i) for i in ids if int(i) < 256 or not skip_special_tokens and int(i) < 256)
        return b.decode("utf-8", errors="replace")

    def save_pretrained(self, path):
        import os

        os.makedirs(path, exist_ok=True)
        open(os.path.join(path, "tokenizer.bytes"), "w").write("byte-level\n")


def tiny_qwen3(seed: int = 0):
    """A 2-layer, 64-wide Qwen3 with random weights (fp32, CPU)."""
    from transformers import Qwen3Config, Qwen3ForCausalLM

    torch.manual_seed(seed)
    cfg = Qwen3Config(vocab_size=VOCAB, hidden_size=64, intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                      num_key_value_heads=2, head_dim=16, max_position_embeddings=4096, bos_token_id=None,
                      eos_token_id=EOS, pad_token_id=PAD, tie_word_embeddings=True)
    return Qwen3ForCausalLM(cfg).float()
