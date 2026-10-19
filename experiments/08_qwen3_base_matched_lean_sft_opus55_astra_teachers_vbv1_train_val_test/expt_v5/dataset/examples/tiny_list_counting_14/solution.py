def solution(x: int, xs: list[int]):
    return sum([1 if a == x else 0 for a in xs])
