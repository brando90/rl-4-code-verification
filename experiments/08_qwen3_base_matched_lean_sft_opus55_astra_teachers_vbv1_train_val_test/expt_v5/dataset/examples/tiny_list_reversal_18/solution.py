def solution(x: int, xs: list[int]):
    return xs[::-1][-1] if xs else x
