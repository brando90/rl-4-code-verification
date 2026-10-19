def solution(xs: list[int], ys: list[int]):
    return [max(a, b) for a, b in zip(xs, ys)]
