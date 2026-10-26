def solution(xs: list[int], ys: list[int]):
    return sum([a + b for a, b in zip(xs, ys)])
