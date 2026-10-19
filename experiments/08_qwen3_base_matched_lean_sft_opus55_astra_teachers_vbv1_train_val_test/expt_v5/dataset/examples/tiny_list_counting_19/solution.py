def solution(x: int, n: int, xs: list[int]):
    return xs[:n].count(x) + xs[n:].count(x)
