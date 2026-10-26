def solution(n: int, xs: list[int]):
    return [a for a in xs[n:] if a > 0]
