"""Normalize single-rank trainer metrics without weakening the v3 positive-gradient gate."""
import math


def single_rank_gradient(value):
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError('one rank gradient norm required')
        value = value[0]
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('finite nonnegative gradient norm required')
    return float(value)
