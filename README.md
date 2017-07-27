# Status
## WORK IN PROGRESS

# Caching

[![Build Status](https://travis-ci.org/bofm/python-caching.svg?branch=master)](https://travis-ci.org/bofm/python-caching)

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
    assert cache.get(1, None) == result
    assert cache.get(2, None) is None

```

# Features

- [x] Memory and file based cache.
- [x] TTL and maxsize.
- [x] Works with `*args`, `**kwargs`.
- [x] Works with mutable function arguments of the following types: `dict`, `list`, `set`.
- [ ] LRS (least recently stored), LRU and LFU cache.
- [ ] Multiprocessing- and thread-safe.
- [ ] Customizable cache key function.
- [ ] Pluggable external caching backends (see Redis example).
