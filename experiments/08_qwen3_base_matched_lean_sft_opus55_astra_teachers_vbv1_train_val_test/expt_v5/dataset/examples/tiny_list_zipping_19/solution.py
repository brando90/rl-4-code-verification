def solution(x: int, xs: list[int], ys: list[int]):
    return [(a + x, b + x) for a, b in zip(xs, ys)]
