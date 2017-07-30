def test_readme(tempdirpath):
    from caching import Cache

    # Set default parameters

    cache = Cache(filepath=f'{tempdirpath}/mycache', ttl=3600, maxsize=1024)

    # Use default parameters

    @cache
    def pow(x, y):
        return x ** y

    # Override default parameters

    @cache(filepath=None, ttl=-1, maxsize=10000)
    def factorial(n):
        if n == 0:
            return 1
        return n * factorial(n - 1)

    def cache_key(x):
        return str(x)

    @cache(ttl=-1, maxsize=10000, key=cache_key)
    def toupper(a):
        return str(a).upper()

    # Using cache as a key-value store

    def calculate_result(*args):
        return args * 2

    try:
        result = cache[1]
    except KeyError:
        result = calculate_result(1)
        cache[1] = result
        assert 1 in cache
        assert cache[1] == result
        assert cache.get(1, None) == result
        assert cache.get(2, None) is None

    # Cleanup

    import os

    cache = Cache(filepath=f'{tempdirpath}/mycache')
    cache[1] = 'one'
    assert 1 in cache
    cache.clear()  # empty the cache
    assert 1 not in cache
    assert list(cache.items()) == []
    assert os.path.isfile(f'{tempdirpath}/mycache')
    cache.remove()  # Empty the cache and remove the underlying file
    assert not os.path.isfile(f'{tempdirpath}/mycache')
