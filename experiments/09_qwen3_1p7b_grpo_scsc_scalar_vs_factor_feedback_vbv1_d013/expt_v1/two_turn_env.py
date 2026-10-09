"""TLDR: Two-turn NeMo environment primitives for the frozen factored-reward experiment."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Literal, Mapping

try:
    import torch
except ImportError:  # The repository's lightweight test interpreter intentionally has no CUDA stack.
    torch = None  # type: ignore[assignment]

from rl4cv.rewards import ScoredResponse, needs_judge, reward_scsc
from prompts_e09 import COMPLETION_REMINDER

try:  # Imported only in the NeMo runtime; pure tests do not need it installed here.
    from nemo_rl.environments.interfaces import EnvironmentInterface, EnvironmentReturn
except ImportError:  # pragma: no cover - permits static/unit tests in the project virtualenv.
    EnvironmentInterface = object  # type: ignore[misc,assignment]
    EnvironmentReturn = None  # type: ignore[assignment]

Arm = Literal["A", "B", "C"]


class RequiredFSCMissing(RuntimeError):
    """A required formal-specification-coverage value was not returned by the validated route."""


@dataclass(frozen=True)
class MeasuredAnswer:
    """One extracted assistant file together with native compiler and judge facts."""

    response: ScoredResponse
    compiler_text: str
    fsc_status: str


Score = Callable[[Mapping[str, Any], str], MeasuredAnswer]


def strict_target(answer: ScoredResponse) -> float:
    """Return the arm-A target: exact conjunction of the same three SCSC factors."""
    if answer.vacuous_theorems or answer.ic_tests != 1.0 or answer.ic_proofs != 1.0:
        return 0.0
    if answer.fsc is None:
        raise RequiredFSCMissing("strict target requires FSC when IC_tests and IC_proofs are both one")
    return 1.0 if answer.fsc == 1.0 else 0.0


def scalar_score(answer: ScoredResponse) -> float:
    """Return gated SCSC, preserving null FSC as a blocking condition when required."""
    if needs_judge(answer, "scsc") and answer.fsc is None:
        raise RequiredFSCMissing("SCSC requires FSC for this extracted compiling proof response")
    return reward_scsc(answer)


def render_feedback(arm: Arm, measured: MeasuredAnswer, *, compiler_limit: int = 2000) -> str:
    """Render the frozen user-feedback payload; C alone receives the named factor vector."""
    if compiler_limit < 0:
        raise ValueError("compiler_limit must be nonnegative")
    answer = measured.response
    s = scalar_score(answer)
    h = strict_target(answer) if answer.ic_tests * answer.ic_proofs else 0.0
    lines = [
        "Verifier feedback for your first attempted Lean solution.",
        f"SCSC={s:.6f}",
        f"strict_complete={int(h)}",
        f"compiler_status={measured.fsc_status}",
        "compiler_output:",
        measured.compiler_text[:compiler_limit],
        "Write a complete replacement Lean solution now. Output only the solution file.",
        COMPLETION_REMINDER,
    ]
    if arm == "C":
        fsc = "null" if answer.fsc is None else f"{answer.fsc:.6f}"
        lines[3:3] = [
            f"IC_tests={answer.ic_tests:.6f}",
            f"IC_proofs={answer.ic_proofs:.6f}",
            f"FSC={fsc}",
        ]
    return "\n".join(lines)


def feedback_sha256(arm: Arm, measured: MeasuredAnswer, *, compiler_limit: int = 2000) -> str:
    """Fingerprint the exact raw observation NeMo tokenizes on turn two."""
    return hashlib.sha256(render_feedback(arm, measured, compiler_limit=compiler_limit).encode()).hexdigest()


def qwen_second_turn_tokens(tokenizer: Any, feedback: str) -> list[int]:
    """Render the raw user feedback plus assistant-generation boundary without double special tokens."""
    rendered = tokenizer.apply_chat_template(
        [{"role": "user", "content": feedback}], tokenize=False, add_generation_prompt=True
    )
    return list(tokenizer(rendered, add_special_tokens=False)["input_ids"])


def qwen_continuation(tokenizer: Any, feedback: str, ended_with_im_end: bool) -> str:
    """Append exact boundaries to preserved sampled tokens, closing capped answers once."""
    prefix = "\n" if ended_with_im_end else "<|im_end|>\n"
    return prefix + tokenizer.apply_chat_template(
        [{"role": "user", "content": feedback}], tokenize=False,
        add_generation_prompt=True, enable_thinking=False,
    )


def assert_action_mask(message_roles: list[str], response_mask: list[int]) -> None:
    """Reject a loss mask that scores prompt/environment tokens or omits assistant actions."""
    if len(message_roles) != len(response_mask):
        raise ValueError("roles and response mask lengths differ")
    for role, masked in zip(message_roles, response_mask):
        if role == "assistant" and masked != 1:
            raise ValueError("assistant action token is absent from loss mask")
        if role != "assistant" and masked != 0:
            raise ValueError("prompt or environment token is present in loss mask")


class TwoTurnLeanEnvironment(EnvironmentInterface):
    """A synchronous NeMo environment that scores only the final assistant file and emits terminal reward once."""

    def __init__(self, arm: Arm, scorer: Score, compiler_limit: int = 2000,
                 tokenizer: Any = None, receipt_dir: str | None = None) -> None:
        if arm not in ("A", "B", "C"):
            raise ValueError(f"unknown arm {arm}")
        self.arm, self.scorer, self.compiler_limit = arm, scorer, compiler_limit
        self.tokenizer = tokenizer
        self.receipt_dir = Path(receipt_dir) if receipt_dir else None

    @staticmethod
    def _last_assistant(log: list[Mapping[str, Any]]) -> str:
        answers = [str(m["content"]) for m in log if m.get("role") == "assistant"]
        if not answers:
            raise ValueError("rollout has no assistant response")
        return answers[-1]

    def step(self, message_log_batch: list[list[Mapping[str, Any]]], metadata: list[dict[str, Any]]):  # type: ignore[override]
        if len(message_log_batch) != len(metadata):
            raise ValueError("messages and metadata batch lengths differ")
        observations: list[dict[str, str]] = []
        next_meta: list[dict[str, Any]] = []
        rewards, terminated, answers = [], [], []
        candidates = [self._last_assistant(log) for log in message_log_batch]
        if hasattr(self.scorer, "score_many"):
            measurements = self.scorer.score_many(metadata, candidates)
            if len(measurements) != len(metadata):
                raise ValueError("incomplete scored batch")
        else:
            measurements = [self.scorer(meta, candidate) for meta, candidate in zip(metadata, candidates)]
        # Validate the complete first/final measurement batch before exposing any
        # reward or writing success receipts; no partial missing-rating update.
        if any(needs_judge(m.response, "scsc") and m.response.fsc is None for m in measurements):
            raise RequiredFSCMissing("required FSC missing: entire batch blocked")
        for candidate, measured, original in zip(candidates, measurements, metadata):
            meta = dict(original)
            turn = int(meta.get("turn", 0))
            if needs_judge(measured.response, "scsc") and measured.response.fsc is None:
                raise RequiredFSCMissing(f"missing FSC for rollout {meta.get('rollout_id', '<unknown>')}")
            if turn == 0:
                meta.update(turn=1, initial_response=candidate, initial_measurement=measured, feedback_sha256=feedback_sha256(self.arm, measured, compiler_limit=self.compiler_limit))
                payload = render_feedback(self.arm, measured, compiler_limit=self.compiler_limit)
                if self.tokenizer is not None:
                    if "last_generated_token_id" not in meta:
                        raise ValueError("actual rollout must supply last sampled token ID")
                    content = qwen_continuation(self.tokenizer, payload,
                        meta["last_generated_token_id"] == self.tokenizer.convert_tokens_to_ids("<|im_end|>"))
                elif EnvironmentReturn is not None:
                    raise ValueError("real NeMo environment requires its actual tokenizer")
                else:
                    content = payload  # Lightweight unit tests only, never admitted runtime.
                meta["rendered_feedback_sha256"] = hashlib.sha256(content.encode()).hexdigest()
                observations.append({"role": "user", "content": content})
                rewards.append(0.0)
                terminated.append(False)
                answers.append(None)
            elif turn == 1:
                reward = strict_target(measured.response) if self.arm == "A" else scalar_score(measured.response)
                meta.update(turn=2, final_response=candidate, final_measurement=measured, final_reward=reward)
                observations.append({"role": "user", "content": ""})
                rewards.append(reward)
                terminated.append(True)
                answers.append(candidate)
            else:
                raise RuntimeError("environment received more than two assistant turns")
            if self.receipt_dir is not None:
                rollout_id = str(meta["rollout_id"])
                safe_id = hashlib.sha256(rollout_id.encode()).hexdigest()
                self.receipt_dir.mkdir(parents=True, exist_ok=True)
                target = self.receipt_dir / f"{safe_id}.turn{turn + 1}.json"
                if target.exists():
                    raise FileExistsError(f"duplicate measurement receipt: {rollout_id} turn {turn + 1}")
                record = {"rollout_id": rollout_id, "task_id": meta["task_id"],
                          "arm": self.arm, "turn": turn + 1,
                          "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
                          "measurement": asdict(measured), "reward": rewards[-1],
                          "terminal": terminated[-1], "generated_tokens": meta.get("generated_tokens"),
                          "last_generated_token_id": meta.get("last_generated_token_id"),
                          "rendered_feedback_sha256": meta.get("rendered_feedback_sha256")}
                temporary = target.with_suffix(".tmp")
                temporary.write_text(json.dumps(record, sort_keys=True) + "\n")
                temporary.replace(target)
            next_meta.append(meta)
        if EnvironmentReturn is None or torch is None:  # pragma: no cover
            return {"observations": observations, "metadata": next_meta, "rewards": rewards, "terminateds": terminated, "answers": answers}
        return EnvironmentReturn(observations, next_meta, [None] * len(next_meta), torch.tensor(rewards), torch.tensor(terminated), answers)

    def global_post_process_and_metrics(self, batch):  # type: ignore[override]
        return batch, {}
