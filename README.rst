Status
======

WORK IN PROGRESS
----------------

Caching
=======

|Build Status| |Coverage Status| |Python Versions|

Python utils and decorators for cаching with TTL, maxsize and file-based storage.

Installation
============

``pip install caching``

Usage
=====

.. code:: python

    from caching import cache

    @cache(ttl=60, maxsize=128, filepath='/tmp/mycache')
    def long_running_function(a, b, *args, c=None, **kwargs):
        pass

Advanced usage
==============

.. code:: python

    from caching import Cache

    # Set default parameters

    cache = Cache(filepath='/tmp/mycache', ttl=3600, maxsize=1024)

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

    @cache(ttl=-1, maxsize=10000, key=cache_key)
    def toupper(a):
        return str(a).upper()

    # Using cache as a key-value store

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

    cache = Cache(filepath='/tmp/mycache')
    cache[1] = 'one'
    assert 1 in cache
    cache.clear()  # empty the cache
    assert 1 not in cache
    assert list(cache.items()) == []
    assert os.path.isfile('/tmp/mycache')
    cache.remove()  # Empty the cache and remove the underlying file
    assert not os.path.isfile('/tmp/mycache')

Features
========

-  [x] Memory and file based cache.
-  [x] TTL and maxsize.
-  [x] Works with ``*args``, ``**kwargs``.
-  [x] Works with mutable function arguments of the following types: ``dict``, ``list``, ``set``.
-  [ ] LRS (least recently stored), LRU and LFU cache.
-  [ ] Multiprocessing- and thread-safe.
-  [ ] Customizable cache key function.
-  [ ] Pluggable external caching backends (see Redis example).

.. |Build Status| image:: https://travis-ci.org/bofm/python-caching.svg?branch=master
   :target: https://travis-ci.org/bofm/python-caching
.. |Coverage Status| image:: https://coveralls.io/repos/github/bofm/python-caching/badge.svg
   :target: https://coveralls.io/github/bofm/python-caching
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/caching.svg
   :target: https://pypi.python.org/pypi/caching
