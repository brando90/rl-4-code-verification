def solution(x: int, y: int, xs: list[int]):
    return [a for a in xs if a < x or a > y]
