def solution(y: int, n: int, xs: list[int]):
    return xs[n] + y if n < len(xs) else y
