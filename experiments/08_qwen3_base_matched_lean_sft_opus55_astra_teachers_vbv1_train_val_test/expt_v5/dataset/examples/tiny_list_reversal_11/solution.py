def solution(x: int, xs: list[int]):
    return [a for a in xs[::-1] if a != x]
