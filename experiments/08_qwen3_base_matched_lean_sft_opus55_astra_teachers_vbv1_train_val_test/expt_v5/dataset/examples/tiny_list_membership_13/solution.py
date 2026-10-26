def solution(xs: list[int], ys: list[int]):
    return all(a in ys for a in xs)
