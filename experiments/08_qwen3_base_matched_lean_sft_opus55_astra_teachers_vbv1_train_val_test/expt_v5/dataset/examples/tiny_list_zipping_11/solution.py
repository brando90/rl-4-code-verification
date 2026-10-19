def solution(xs: list[int], ys: list[int]):
    return [(b, a) for a, b in zip(xs, ys)]
