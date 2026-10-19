def solution(xs: list[int], ys: list[int]):
    return all(a == b for a, b in zip(xs, ys))
