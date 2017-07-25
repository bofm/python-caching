# Status
## WORK IN PROGRESS

# Caching

Python utils and decorators for cаching.

# Installation

`pip install caching`

# Usage

```python
from caching import cache

@cache(ttl=60, maxsize=128, filepath='/tmp/mycache')
def long_running_function(a, b, c=None, *kwargs):
    pass
```

# Advanced usage

```python
from caching import Cache

# Set default parameters
cache = Cache(filepath='/tmp/mycache', ttl=3600, maxsize=1024, typed=True)

# Use default parameters

@cache
def pow(x, y):
    return x**y

# Override default parameters

@cache(filepath=None, ttl=-1, maxsize=10000)
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)

def cache_key(x):
    return str(x)

@cache(ttl=-1, maxsize=10000, typed=False, key=cache_key)
def toupper(a):
    return str(a).upper()

# Using cache as a key-value storage

try:
    result = cache[1]
except KeyError:
    result = calculate_result(1)
    cache[1] = result
    assert 1 in cache
    assert cache[1] == result

# Non-Pythonic usage

def myapp():
    ...
    value = 123
    cache_key = 'some_func_%s' % value
    try:
        result = cache.get(cache_key)
    except CacheMiss:
        result = some_func(value)
        cache.put(cache_key, value)

```

# Features

- [ ] Memory and file based cache.
- [ ] TTL and maxsize.
- [ ] Works with `*args`, `**kwargs`.
- [ ] Works with mutable function arguments of the following types: `dict`, `list`, `set`.
- [ ] Multiprocessing- and thread-safe.
- [ ] Customizable cache key function.
- [ ] LRU or LFU cache.
- [ ] Pluggable external caching backends (see Redis example).
