def solution(x: int, xs: list[int]):
    return all(a != x for a in xs)
