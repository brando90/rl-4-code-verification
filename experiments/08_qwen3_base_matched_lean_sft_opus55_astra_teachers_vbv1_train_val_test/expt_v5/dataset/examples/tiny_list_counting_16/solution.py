def solution(x: int, y: int, xs: list[int]):
    return [a + y for a in xs].count(x + y)
