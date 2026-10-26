def solution(x: int, n: int, xs: list[int]):
    return xs[:n][-1] if xs[:n] else x
