def solution(xs: list[int], ys: list[int]):
    return set(xs).union(ys).issuperset(xs)
