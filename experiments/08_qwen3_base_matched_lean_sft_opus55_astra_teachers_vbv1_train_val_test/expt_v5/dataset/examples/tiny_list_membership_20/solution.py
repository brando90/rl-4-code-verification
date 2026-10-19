def solution(x: int, xs: list[int]):
    return x in [a for a in xs if a >= 0]
