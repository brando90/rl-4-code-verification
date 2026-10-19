def solution(x: int, xs: list[int]):
    return len(set(xs).difference([x]))
