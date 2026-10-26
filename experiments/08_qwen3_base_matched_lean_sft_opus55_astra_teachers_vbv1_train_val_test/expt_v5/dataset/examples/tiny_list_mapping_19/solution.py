def solution(x: int, xs: list[int], p: bool):
    return [a + x if p else a - x for a in xs]
