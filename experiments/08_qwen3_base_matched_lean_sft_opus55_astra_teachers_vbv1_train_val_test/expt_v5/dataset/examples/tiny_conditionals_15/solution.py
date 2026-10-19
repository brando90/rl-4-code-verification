def solution(x: int, y: int, z: int, p: bool, q: bool):
    return x if p else (y if q else z)
