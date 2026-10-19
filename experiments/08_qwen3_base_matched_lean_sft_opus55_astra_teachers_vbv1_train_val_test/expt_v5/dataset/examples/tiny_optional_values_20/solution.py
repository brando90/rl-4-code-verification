def solution(x: int, opt: int | None):
    return None if opt is None else (opt if opt <= x else x)
