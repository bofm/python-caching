import os

import pytest
import time

from caching import SQLiteStorage


@pytest.fixture
def storage(tmpdir):
    filepath = f'{tmpdir}/cache'
    with SQLiteStorage(
        filepath=filepath,
        ttl=60,
        maxsize=100,
    ) as s:
        assert os.path.isfile(filepath)
        yield s


def test_repr(tmpdir):
    filepath = f'{tmpdir}/cache'
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


def test_ttl_gt0(tmpdir):
    storage = SQLiteStorage(
        filepath=f'{tmpdir}/cache',
        ttl=0.001,
        maxsize=100,
    )
    storage[b'1'] = b'one'
    time.sleep(0.0011)
    assert storage.get(b'1') is None

    storage = SQLiteStorage(
        filepath=f'{tmpdir}/cache',
        ttl=99,
        maxsize=100,
    )
    storage[b'x'] = b'x'
    assert storage[b'x'] == b'x'


@pytest.mark.parametrize('ttl', (0, -1, -100, -0.5, -1.5))
def test_ttl_lte0(tmpdir, ttl):
    with SQLiteStorage(
        filepath=f'{tmpdir}/cache',
        ttl=ttl,
        maxsize=100,
    ) as storage:
        storage[b'1'] = b'one'
        assert storage.get(b'1') == b'one'

        with storage.db as db:
            db.execute(f'UPDATE cache SET ts = ts - {ttl + 10}')

        storage[b'x'] = b'x'
        assert storage.get(b'1') == b'one'


def test_maxsize(tmpdir):
    with SQLiteStorage(
        filepath=f'{tmpdir}/cache',
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


def test_remove(tmpdir):
    tmpdir = str(tmpdir)
    assert os.listdir(tmpdir) == []
    filepath = f'{tmpdir}/cache'
    storage = SQLiteStorage(filepath=filepath, ttl=-1, maxsize=10)
    assert os.path.isfile(filepath)
    assert os.listdir(tmpdir) == ['cache']
    storage.remove()
    assert not os.path.isfile(filepath)
    assert os.listdir(tmpdir) == []


def test_items(storage):
    storage[b'1'] = b'one'
    storage[b'2'] = b'two'

    assert storage[b'1'] == b'one'
    assert storage[b'2'] == b'two'

    items = [item for item in storage.items()]

    assert items == [
        (b'1', b'one'),
        (b'2', b'two'),
    ]


def ensure_index(db, table_name, columns, unique):
    columns = ', '.join(columns)
    unique = 'UNIQUE' if unique else ''
    query = (
        f'SELECT * FROM SQLITE_MASTER '
        f"WHERE TYPE = 'index' AND tbl_name = '{table_name}'"
        f" AND sql LIKE '%{unique} INDEX % ON {table_name} ({columns})'"
    )
    rows = db.execute(query).fetchall()
    assert len(rows) == 1


def test_schema_fifo():
    storage = SQLiteStorage(
        ttl=1,
        maxsize=1,
        policy='FIFO',
        filepath=':memory:',
    )

    def q(*args):
        return storage.db.execute(*args).fetchall()

    ensure_index(storage.db, 'cache', ['ts'], False)
    assert len(q(
        'SELECT * FROM SQLITE_MASTER '
        "WHERE TYPE = 'trigger' AND tbl_name = 'cache'",
    )) == 1


def test_schema_lru():
    storage = SQLiteStorage(
        ttl=1,
        maxsize=1,
        policy='LRU',
        filepath=':memory:',
    )

    def q(*args):
        return storage.db.execute(*args).fetchall()

    ensure_index(storage.db, 'cache', ['ts'], False)
    ensure_index(storage.db, 'cache', ['used', 'ts'], False)
    assert len(q(
        'SELECT * FROM SQLITE_MASTER '
        "WHERE TYPE = 'trigger' AND tbl_name = 'cache'",
    )) == 1


def test_schema_lfu():
    storage = SQLiteStorage(
        ttl=1,
        maxsize=1,
        policy='LFU',
        filepath=':memory:',
    )

    def q(*args):
        return storage.db.execute(*args).fetchall()

    ensure_index(storage.db, 'cache', ['ts'], False)
    ensure_index(storage.db, 'cache', ['used', 'ts'], False)
    assert len(q(
        'SELECT * FROM SQLITE_MASTER '
        "WHERE TYPE = 'trigger' AND tbl_name = 'cache'",
    )) == 1
