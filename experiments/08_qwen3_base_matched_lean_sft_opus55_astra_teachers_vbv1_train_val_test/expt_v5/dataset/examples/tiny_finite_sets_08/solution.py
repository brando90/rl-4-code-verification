def solution(x: int, xs: list[int], ys: list[int]):
    return x in set(xs).intersection(ys)
