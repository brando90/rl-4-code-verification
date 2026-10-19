def solution(xs: list[int]):
    return all(a % 2 == 0 for a in xs)
