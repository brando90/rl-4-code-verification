"""TLDR: Prospective completion reminder shared by every experiment09 initial/continuation prompt."""

COMPLETION_REMINDER = (
    "Solve the entire assigned task, including every required file, question and subtask. "
    "Produce the complete required Lean deliverable in the specified response format; an outline, "
    "partial draft, progress report or claim of completion is not a substitute. Inspect your final "
    "response for completeness. You have no execution tools: do not claim to have run checks, tests "
    "or compilation. Within the declared token and two-turn limits, continue working and fixing "
    "errors until the requirements are met or a declared terminal condition is reached. Follow "
    "the fixed continuation procedure without resetting budgets. If anything remains unresolved, "
    "preserve the best current Lean deliverable and note remaining failures in Lean comments; "
    "never claim success or invent verification."
)


def initial_messages(prompt):
    messages = prompt.messages()
    messages[-1] = {**messages[-1], 'content': messages[-1]['content'] + '\n\n' + COMPLETION_REMINDER}
    return messages
