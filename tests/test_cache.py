import os
import time

import pytest

from caching import Cache


@pytest.fixture(params=[False, True], ids=['memory', 'file'])
def cache(tempdirpath, request):
    filepath = request.param and f'{tempdirpath}/cache' or None
    with Cache(filepath=filepath) as c:
        yield c


def test_repr():
    c = Cache(maxsize=1, ttl=1, filepath=None, typed=True, x='y')
    expected = "Cache(maxsize=1, ttl=1, filepath=None, typed=True, x='y')"
    assert repr(c) == expected


keys_and_values = [
    (1, 'one'),
    (1, 2),
    ('1', 2),
    (b'1', b'one'),
    (1, 0.1),
    (0.1, 1),
    ('a', 'b'),
    ('a' * 999999, 'b' * 999999),
    ([1, 'a'], {'b': 'c'}),
    ({'b': 'c'}, [1, 'a']),
    ({'b': 'c'}, {1, None, '555'}),
    ({'b', 'c'}, (1, 'z')),
]
test_names = [
    None if len(str((k,v))) < 30 else f'{str(k)[:10]}_{str(v)[:10]}'
    for k, v in keys_and_values
]


@pytest.mark.parametrize('key, value', keys_and_values, ids=test_names)
def test_cache_set_get_in_clear_del(cache, key, value):
    with pytest.raises(KeyError):
        cache[key]
    cache[key] = value
    assert cache[key] == value
    # Assert duplicate erors are handled
    cache[key] = value
    assert cache[key] == value
    assert key in cache
    assert -999 not in cache
    cache.clear()
    assert cache.get(key) is None
    cache[key] = value
    assert cache[key] == value
    del cache[key]
    assert cache.get(key) is None
    with pytest.raises(KeyError):
        del cache[key]


def test_duplicates(cache):
    assert 1 not in cache
    cache[1] = 'one'
    assert 1 in cache
    assert cache[1] == 'one'
    cache[1] = '1'
    assert cache[1] == '1'


def test_function_decorator_noargs(cache):
    call_count = 0

    @cache
    def pow(a, b):
        time.sleep(0.001)  # to make timestamp different in each call
        nonlocal call_count
        call_count += 1
        return a**b

    def values():
        return list(cache.decode(v) for k, v in cache.storage.items())

    assert call_count == 0

    assert pow(2, 3) == 8
    assert call_count == 1
    expected_values = [8]
    assert values() == expected_values

    assert pow(2, 3) == 8
    assert call_count == 1
    assert values() == expected_values

    assert pow(2, 2) == 4
    assert call_count == 2
    expected_values = [8, 4]
    assert values() == expected_values

    assert pow(2, 2) == 4
    assert call_count == 2
    assert values() == expected_values


@pytest.mark.skip
def test_function_decorator_with_args(cache):
    assert 0


@pytest.mark.skip
def test_copy():
    assert 0


def test_raises_if_closed(cache):
    cache.close()
    cache.close()
    with pytest.raises(Exception):
        cache[1] = 1
    with pytest.raises(Exception):
        cache[1]
    with pytest.raises(Exception):
        cache.get(1)
    with pytest.raises(Exception):
        cache.get(1, None)
    with pytest.raises(Exception):
        del cache[1]
    with pytest.raises(Exception):
        cache[1] = 1


def test_remove(tempdirpath, cache):
    cache.remove()
    filepath = f'{tempdirpath}/cache'
    cache = Cache(filepath=filepath)
    assert os.path.isfile(filepath)
    assert os.listdir(tempdirpath) == ['cache']
    cache[1] = 'one'
    cache[2] = 'two'
    assert os.path.isfile(filepath)
    assert os.listdir(tempdirpath) == ['cache']
    cache.remove()
    assert not os.path.isfile(filepath)
    assert os.listdir(tempdirpath) == []


@pytest.mark.skip
def test_typed():
    assert 0


@pytest.mark.skip
def test_make_key():
    assert 0
