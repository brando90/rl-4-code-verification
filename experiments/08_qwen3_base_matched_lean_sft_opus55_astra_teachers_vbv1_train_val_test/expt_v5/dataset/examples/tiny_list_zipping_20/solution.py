def solution(xs: list[int], ys: list[int]):
    return [abs(a - b) for a, b in zip(xs, ys)]
