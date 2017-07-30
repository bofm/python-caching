import pickle
from collections import OrderedDict
from functools import wraps

from .storage import SQLiteStorage

MISS = object()

# Something unique and equal to itself after pickling-unpickling
# and unlikely to appear in args
KWARGS_MARK = '☭'


def make_key(*args, **kwargs):
    global KWARGS_MARK
    if kwargs:
        return (
            *args,
            KWARGS_MARK,
            *(x for kv in sorted(kwargs.items()) for x in kv),
        )
    else:
        return args


def _type_names(args, kwargs):
    arg_type_names = *map(_type_name, args),
    kwarg_type_names = *(_type_name(v) for k, v in sorted(kwargs.items())),
    return arg_type_names, kwarg_type_names


def _type_name(obj):
    klass = type(obj)
    return f'{klass.__module__}.{klass.__qualname__}'


def _function_name(fn):
    return f'{fn.__module__}.{fn.__qualname__}'


class Cache:

    def __init__(
        self,
        *,
        maxsize=1024,
        ttl=-1,
        filepath=None,
        typed=False,
        key=make_key,
        **kwargs
    ):
        self.params = OrderedDict(
            maxsize=maxsize,
            ttl=ttl,
            filepath=filepath,
            typed=typed,
            key=key,
            **kwargs
        )
        self.typed = typed
        self.make_key = key
        self.storage = SQLiteStorage(
            filepath=filepath or ':memory:',
            ttl=ttl,
            maxsize=maxsize,
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"({', '.join(f'{k}={repr(v)}' for k,v in self.params.items())})"
        )

    def _decorator(self, fn):
        if not callable(fn):
            raise TypeError(f'{fn} is not callable')

        key_prefix = _function_name(fn)
        make_key_ = self.typed and self._make_key_typed or self.make_key

        @wraps(fn)
        def wrapper(*args, **kwargs):
            global MISS
            nonlocal self, key_prefix, make_key_, fn
            key = (key_prefix, *make_key_(*args, **kwargs))
            # Something unique is needed here.
            # None is not an option because fn may return None. So MISS is used
            res = self.get(key, MISS)
            if res is MISS:
                res = self[key] = fn(*args, **kwargs)
            return res
        wrapper._cache = self
        return wrapper

    def __call__(self, fn=None, **kwargs):
        if fn is None and kwargs:
            return self.copy(**kwargs)(fn)
        elif callable(fn) and not kwargs:
            return self._decorator(fn)
        else:
            return self._decorator

    def __getitem__(self, key):
        return self.decode(self.storage[self.encode(key)])

    def __setitem__(self, key, value):
        self.storage[self.encode(key)] = self.encode(value)

    def __delitem__(self, key):
        del self.storage[self.encode(key)]

    def __contains__(self, key):
        global MISS
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

    def _make_key_typed(self, *args, **kwargs):
        return _type_names(args, kwargs), self.make_key(*args, **kwargs)

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


cache = Cache()
