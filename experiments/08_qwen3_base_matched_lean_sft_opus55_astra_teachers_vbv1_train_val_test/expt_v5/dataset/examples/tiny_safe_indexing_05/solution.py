def solution(x: int, xs: list[int]):
    return xs[-2] if len(xs) > 1 else x
