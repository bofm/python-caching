def test_readme(tempdirpath):

    from caching import Cache

    # One cache for many functions

    cache = Cache(filepath=f'{tempdirpath}/mycache', ttl=3600, maxsize=1024)

    @cache
    def pow(x, y):
        return x**y

    @cache
    def factorial(n):
        if n == 0:
            return 1
        return n * factorial(n - 1)

        # Custom cache key

    def cache_key(x):
        return str(x)

    cache = Cache(key=cache_key)
    call_count = 0

    @cache
    def toupper(a):
        nonlocal call_count
        call_count += 1
        return str(a).upper()

    @cache
    def tolower(a):
        nonlocal call_count
        call_count += 1
        return str(a).lower()

    # The key function returns the same result for both 1 and '1'
    assert toupper('1') == toupper(1)
    assert call_count == 1

    # Using cache as a key-value store

    cache = Cache()

    try:
        result = cache[1]
    except KeyError:
        def calculate_result(x):
            return x

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
