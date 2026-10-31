"""Format checks for train_v28.py (run locally; needs network once for the tokenizers).

usage: python tests/test_formats.py   (from the experiment dir; numpy, transformers, torch importable)
Checks per family: BOS appears once, the prompt is exactly the template's text, the assistant ids end with turn-end + EOS,
the template saved with the checkpoint renders the same prompt as training used, generation stop tokens are single tokens.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import train_v28 as t  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

ROW = {"system": "You are a Lean 4 expert.", "user": "Translate this Python function:\n\ndef f(x):\n    return x + 1\n",
       "assistant": "```lean\ndef f (x : Nat) : Nat := x + 1\n```"}
EXPECT = {
    "llama3": ("<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
               "<|start_header_id|>assistant<|end_header_id|>\n\n", "<|eot_id|>"),
    "gemma3": ("<start_of_turn>user\n{system}\n\n{user}<end_of_turn>\n<start_of_turn>model\n", "<end_of_turn>\n"),
}
for arm in ("llama1b", "gemma1b"):
    spec = t.ARMS[arm]
    fam = spec["family"]
    tok = AutoTokenizer.from_pretrained(spec["model"], revision=spec["revision"])
    pids, aids = t.format_ids(tok, fam, ROW)
    want_prefix, turn_end = EXPECT[fam]
    want_prefix = want_prefix.format(**ROW)
    assert pids[0] == tok.bos_token_id and pids.count(tok.bos_token_id) == 1, "BOS must appear exactly once"
    assert tok.decode(pids[1:], skip_special_tokens=False) == want_prefix, (tok.decode(pids[1:]), want_prefix)
    assert tok.decode(aids, skip_special_tokens=False) == ROW["assistant"] + turn_end + tok.eos_token
    assert aids[-1] == tok.eos_token_id
    # the saved template, as vLLM generation will apply it (text, then tokenizer adds BOS once)
    tok.chat_template = t.FAMILIES[fam]["template"]
    text = tok.apply_chat_template([{"role": "system", "content": ROW["system"]}, {"role": "user", "content": ROW["user"]}],
                                   tokenize=False, add_generation_prompt=True, enable_thinking=True)
    assert text == want_prefix and tok.encode(text, add_special_tokens=True) == pids
    for s in t.FAMILIES[fam]["stop_tokens"]:
        i = tok.convert_tokens_to_ids(s)
        assert i is not None and i != tok.unk_token_id and tok.decode([i], skip_special_tokens=False) == s, s
    print(fam, "OK", {"prompt_tokens": len(pids), "assistant_tokens": len(aids), "bos": tok.bos_token_id, "eos": tok.eos_token_id,
                      "pad": tok.pad_token, "stop": t.FAMILIES[fam]["stop_tokens"]})
# 1B and 3B share tokenizer files (same Hub LFS sha), so one token file per family is valid
assert t.ARMS["llama1b"]["lfs_sha256"]["tokenizer.json"] == t.ARMS["llama3b"]["lfs_sha256"]["tokenizer.json"]
assert t.ARMS["gemma1b"]["lfs_sha256"]["tokenizer.json"] == t.ARMS["gemma4b"]["lfs_sha256"]["tokenizer.json"]
print("formats OK")
