from distribcalc import tasks


def test_is_prime_small_values():
    assert not tasks.is_prime(0)
    assert not tasks.is_prime(1)
    assert tasks.is_prime(2)
    assert tasks.is_prime(3)
    assert not tasks.is_prime(4)


def test_primes_in_range():
    assert tasks.primes_in_range(1, 10) == [2, 3, 5, 7]
    assert tasks.primes_in_range(10, 1) == [2, 3, 5, 7]


def test_count_primes():
    assert tasks.count_primes(1, 10) == 4
    assert tasks.count_primes(10, 20) == 4
