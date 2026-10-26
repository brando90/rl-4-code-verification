def solution(x: int, n: int, xs: list[int]):
    return xs[::-1][n] if n < len(xs) else x
