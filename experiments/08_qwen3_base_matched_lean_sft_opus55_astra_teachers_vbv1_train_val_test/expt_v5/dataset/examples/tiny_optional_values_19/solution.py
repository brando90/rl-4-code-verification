def solution(x: int, p: bool, opt: int | None):
    return opt if opt is not None else (x if p else None)
