"""Computational tasks executed by the worker processes."""
from __future__ import annotations

from math import isqrt
from typing import List


def is_prime(n: int) -> bool:
    """Return True if *n* is a prime number."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    limit = isqrt(n)
    k = 5
    step = 2
    while k <= limit:
        if n % k == 0:
            return False
        k += step
        step = 6 - step  # alternates between checking n+2 and n+4
    return True


def primes_in_range(start: int, end: int) -> List[int]:
    """Return all prime numbers in the closed interval [start, end]."""
    if start > end:
        start, end = end, start
    primes = []
    for value in range(start, end + 1):
        if is_prime(value):
            primes.append(value)
    return primes


def count_primes(start: int, end: int) -> int:
    """Return the number of primes in the closed interval [start, end]."""
    return len(primes_in_range(start, end))


