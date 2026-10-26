def solution(x: int, n: int, xs: list[int], ys: list[int]):
    return (xs + ys)[n] if n < len(xs + ys) else x
