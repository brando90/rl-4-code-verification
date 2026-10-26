def solution(x: int, xs: list[int]):
    return any(a != x for a in xs)
