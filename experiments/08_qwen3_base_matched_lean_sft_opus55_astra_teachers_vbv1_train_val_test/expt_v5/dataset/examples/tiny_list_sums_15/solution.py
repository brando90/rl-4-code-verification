def solution(n: int, xs: list[int]):
    return sum(xs[:n]) + sum(xs[n:])
