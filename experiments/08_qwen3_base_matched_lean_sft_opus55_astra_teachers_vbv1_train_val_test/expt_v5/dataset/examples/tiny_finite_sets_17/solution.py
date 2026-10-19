def solution(xs: list[int], ys: list[int]):
    return set(xs).union(ys) == set(ys).union(xs)
