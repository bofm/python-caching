import os

import pytest

from caching import SQLiteStorage


@pytest.fixture
def storage(tempdirpath):
    filepath = f'{tempdirpath}/cache'
    with SQLiteStorage(
        filepath=filepath,
        ttl=60,
        maxsize=100,
    ) as s:
        assert os.path.isfile(filepath)
        yield s


def test_repr(tempdirpath):
    filepath = tempdirpath + '/cache'
    storage = SQLiteStorage(maxsize=1, ttl=1, filepath=filepath)
    expected = f"SQLiteStorage(filepath='{filepath}', maxsize=1, ttl=1)"
    assert repr(storage) == expected


def test_set_get(storage):
    storage[b'1'] = b'one'
    assert storage[b'1'] == b'one'
    # Assert duplicate erors are handled
    storage[b'1'] = b'one'
    assert storage[b'1'] == b'one'
    with pytest.raises(KeyError):
        storage[b'2']
    no = object()
    assert storage.get(b'3') is None
    assert storage.get(b'3', no) is no
    storage[b'1'] = b'one'
    assert storage[b'1'] == b'one'
    del storage[b'1']
    assert storage.get(b'1') is None
    with pytest.raises(KeyError):
        del storage[b'1']


def test_ttl_gt0(tempdirpath):
    storage = SQLiteStorage(
        filepath=f'{tempdirpath}/cache',
        ttl=100,
        maxsize=100,
    )
    storage[b'1'] = b'one'
    assert storage[b'1'] == b'one'

    with storage.db as db:
        db.execute(f'UPDATE cache SET ts = ts - {storage.ttl + 0.01}')

    storage[b'x'] = b'x'

    res = storage.get(b'1')
    assert res is None


@pytest.mark.parametrize('ttl', (0, -1, -100, -0.5, -1.5))
def test_ttl_lte0(tempdirpath, ttl):
    with SQLiteStorage(
        filepath=f'{tempdirpath}/cache',
        ttl=ttl,
        maxsize=100,
    ) as storage:
        storage[b'1'] = b'one'
        assert storage.get(b'1') == b'one'

        with storage.db as db:
            db.execute(f'UPDATE cache SET ts = ts - {ttl + 10}')

        storage[b'x'] = b'x'
        assert storage.get(b'1') == b'one'


def test_maxsize(tempdirpath):
    with SQLiteStorage(
        filepath=f'{tempdirpath}/cache',
        ttl=-1,
        maxsize=2,
    ) as storage:
        storage[b'1'] = b'one'
        storage[b'2'] = b'two'

        assert storage[b'1'] == b'one'
        assert storage[b'2'] == b'two'

        storage[b'3'] = b'three'

        assert storage.get(b'1') is None
        assert storage.get(b'2') == b'two'
        assert storage.get(b'3') == b'three'

        storage[b'4'] = b'four'

        assert storage.get(b'1') is None
        assert storage.get(b'2') is None
        assert storage.get(b'3') == b'three'
        assert storage.get(b'4') == b'four'


def test_clear(storage):
    storage[b'1'] = b'one'
    storage[b'2'] = b'two'

    assert storage[b'1'] == b'one'
    assert storage[b'2'] == b'two'

    storage.clear()

    assert storage.get(b'1') is None
    assert storage.get(b'2') is None


def test_remove(tempdirpath):
    assert os.listdir(tempdirpath) == []
    filepath = f'{tempdirpath}/cache'
    storage = SQLiteStorage(filepath=filepath, ttl=-1, maxsize=10)
    assert os.path.isfile(filepath)
    assert os.listdir(tempdirpath) == ['cache']
    storage.remove()
    assert not os.path.isfile(filepath)
    assert os.listdir(tempdirpath) == []


def test_items(storage):
    storage[b'1'] = b'one'
    storage[b'2'] = b'two'

    assert storage[b'1'] == b'one'
    assert storage[b'2'] == b'two'

    items = []
    for item in storage.items():
        items.append(item)

    assert items == [
        (b'1',  b'one'),
        (b'2', b'two'),
    ]
