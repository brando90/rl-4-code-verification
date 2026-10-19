def solution(xs: list[int], ys: list[int]):
    return any(a in ys for a in xs)
