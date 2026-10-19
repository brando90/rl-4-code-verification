def solution(xs: list[int], ys: list[int]):
    return [min(a, b) for a, b in zip(xs, ys)]
