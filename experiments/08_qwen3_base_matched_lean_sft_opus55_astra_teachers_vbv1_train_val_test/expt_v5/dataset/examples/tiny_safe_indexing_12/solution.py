def solution(x: int, n: int, xs: list[int]):
    return xs[n] == x if n < len(xs) else False
