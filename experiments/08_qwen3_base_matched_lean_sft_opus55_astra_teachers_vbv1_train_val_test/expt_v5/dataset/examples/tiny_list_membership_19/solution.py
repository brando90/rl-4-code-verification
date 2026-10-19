def solution(x: int, y: int, xs: list[int]):
    return x in [a + y for a in xs]
