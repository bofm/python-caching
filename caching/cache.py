import pickle
from collections import OrderedDict
from functools import wraps

from caching.storage import SQLiteStorage


MISS = object()


class Cache:

    def __init__(self, *, maxsize=1024, ttl=-1, filepath=None, typed=False, **kwargs):
        self.params = OrderedDict(
            maxsize=maxsize,
            ttl=ttl,
            filepath=filepath,
            typed=typed,
        )
        self.typed = typed
        self.params.update(kwargs)
        self.storage = SQLiteStorage(
            filepath=filepath or ':memory:',
            ttl=ttl,
            maxsize=maxsize,
        )
        self.make_key = make_key

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"({', '.join(f'{k}={repr(v)}' for k,v in self.params.items())})"
        )

    def __call__(self, fn=None, **kwargs):
        def decorator(fn):

            key_prefix = self.make_key_prefix(fn)

            @wraps(fn)
            def wrapper(*args, **kwargs):
                key = self.make_key(self.typed, key_prefix, *args, **kwargs)
                res = self.get(key, MISS)
                if res is MISS:
                    res = self[key] = fn(*args, **kwargs)
                return res

            return wrapper

        if fn is None and kwargs:
            return self.copy(**kwargs)(fn)
        elif callable(fn) and not kwargs:
            return decorator(fn)
        else:
            return decorator

    def __getitem__(self, key):
        return self.decode(self.storage[self.encode(key)])

    def __setitem__(self, key, value):
        self.storage[self.encode(key)] = self.encode(value)

    def __delitem__(self, key):
        del self.storage[self.encode(key)]

    def __contains__(self, key):
        return self.get(key, MISS) is not MISS

    def get(self, key, default=None):
        res = self.storage.get(self.encode(key), default)
        if res is not default:
            res = self.decode(res)
        return res

    def clear(self):
        self.storage.clear()

    def close(self):
        self.storage.close()

    def copy(self, **kwargs):
        return self.__class__(**{**self.params, **kwargs})

    def make_key_prefix(self, fn):
        return function_name(fn)

    def encode(self, obj):
        return pickle.dumps(obj)

    def decode(self, data):
        return pickle.loads(data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.storage.close()

    def remove(self):
        self.storage.remove()


def make_key(typed=False, *args, **kwargs):
    kwargs = sorted(kwargs.items())
    if typed:
        args = tuple((a, type_name(a)) for a in args)
        kwargs = tuple(((k, type_name(k)), (v, type_name(v)))
                       for k, v in kwargs)
    return f'{args}{kwargs}'


def type_name(obj):
    klass = type(obj)
    return f'{klass.__module__}.{klass.__qualname__}'


def function_name(fn):
    return  f'{fn.__module__}.{fn.__qualname__}'


cache = Cache()
