def solution(xs: list[int], ys: list[int]):
    return all(a >= 0 for a in xs + ys)
