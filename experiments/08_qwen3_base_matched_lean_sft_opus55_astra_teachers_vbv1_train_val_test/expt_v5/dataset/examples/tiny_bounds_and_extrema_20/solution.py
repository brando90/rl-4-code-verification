def solution(x: int, y: int, z: int):
    return max(min(x, y), min(x, z))
