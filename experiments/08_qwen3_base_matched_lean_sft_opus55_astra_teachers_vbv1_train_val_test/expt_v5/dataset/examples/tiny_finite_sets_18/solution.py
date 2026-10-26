def solution(xs: list[int], ys: list[int]):
    return set(xs).intersection(ys) == set(ys).intersection(xs)
