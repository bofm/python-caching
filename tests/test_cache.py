import os
import time

import pytest

from caching import Cache
from caching.cache import _type_name, _function_name, _type_names, make_key


@pytest.fixture(params=[False, True], ids=['memory', 'file'])
def cache(tempdirpath, request):
    filepath = request.param and f'{tempdirpath}/cache' or None
    with Cache(filepath=filepath) as c:
        yield c


def test_repr():
    c = Cache(maxsize=1, ttl=1, filepath=None, typed=True, x='y')
    expected = ("Cache(maxsize=1, ttl=1, filepath=None, typed=True, "
                f"key={make_key}, x='y')")
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
    None if len(str((k, v))) < 30 else f'{str(k)[:10]}_{str(v)[:10]}'
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


def test_typed(cache):
    assert 1.0 == 1
    assert make_key(1.0) == make_key(1)
    assert _type_name(1.0) != _type_name(1)
    assert _type_names((1.0,), {}) != _type_names((1,), {})

    call_count = 0

    @cache
    def func(a):
        nonlocal call_count
        call_count += 1
        return a

    assert call_count == 0
    assert func(1) == 1
    assert call_count == 1
    assert func(1) == 1
    assert call_count == 1
    assert func(1.0) == 1.0
    assert call_count == 2
    assert isinstance(func(1.0), float)
    assert call_count == 2


@pytest.mark.skip
def test_make_key():
    assert 0


@pytest.mark.parametrize('obj, expected', [
    (1, 'builtins.int'),
    ('', 'builtins.str'),
    ([], 'builtins.list'),
    ({}, 'builtins.dict'),
    (set(), 'builtins.set'),
    (object(), 'builtins.object'),
    (os, 'builtins.module'),
    (lambda: 1, 'builtins.function'),
    (Cache().get, 'builtins.method'),
    (Cache, 'builtins.type'),
    (None, 'builtins.NoneType'),
])
def test__type_name(obj, expected):
    assert _type_name(obj) == expected


def test__type_names():
    def test(expected, *args, **kwargs):
        assert _type_names(args, kwargs) == expected

    expected = (
        ('builtins.str', 'builtins.int',),
        ('builtins.list', 'builtins.int'),
    )
    test(expected, 'a', 1, one=1, l=[1, 2])


@pytest.mark.parametrize('obj, expected', [
    (lambda: 1, f'{__name__}.<lambda>'),
    (cache, f'{__name__}.cache'),
])
def test__function_name(obj, expected):
    assert _function_name(obj) == expected
