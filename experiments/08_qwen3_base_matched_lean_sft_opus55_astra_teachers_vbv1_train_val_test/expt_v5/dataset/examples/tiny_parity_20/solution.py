def solution(xs: list[int]):
    return any(a % 2 != 0 for a in xs)
