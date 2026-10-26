def solution(xs: list[int], ys: list[int]):
    return any(a == b for a, b in zip(xs, ys))
