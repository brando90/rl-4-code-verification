def solution(x: int, y: int, z: int):
    return x if x >= y and x >= z else max(y, z)
