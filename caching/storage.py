import os
import sqlite3
from contextlib import suppress
from typing import Generator, Tuple, Union


class CacheStorageBase:

    def __init__(self, *, maxsize, ttl):
        self.maxsize = maxsize
        self.ttl = ttl

    def __setitem__(self, key, value) -> None:
        raise NotImplementedError  # pragma: no cover

    def __getitem__(self, key) -> bytes:
        raise NotImplementedError  # pragma: no cover

    def __delitem__(self, key) -> None:
        raise NotImplementedError  # pragma: no cover

    def get(self, key, default=None) -> Union[bytes, None]:
        raise NotImplementedError  # pragma: no cover

    def clear(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def remove(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def items(self) -> Generator[Tuple[bytes, bytes], None, None]:
        raise NotImplementedError  # pragma: no cover


class SQLiteStorage(CacheStorageBase):
    SQLITE_TIMESTAMP = "(julianday('now') - 2440587.5)*86400.0"

    def __init__(self, *, filepath, ttl, maxsize):
        super(SQLiteStorage, self).__init__(ttl=ttl, maxsize=maxsize)
        self.filepath = filepath
        self.db = sqlite3.connect(filepath, isolation_level='DEFERRED')
        self.init_db()
        self.nothing = object()

        if self.ttl > 0:
            ttl_filter = f' AND ({self.SQLITE_TIMESTAMP} - ts) <= {self.ttl}'
        else:
            ttl_filter = ''

        self.sql_select = f'SELECT value FROM cache WHERE key = ?{ttl_filter}'
        self.sql_delete = 'DELETE FROM cache WHERE key = ?'
        self.sql_insert = (
            "INSERT OR REPLACE INTO cache VALUES "
            f"(?, {self.SQLITE_TIMESTAMP}, ?)"
        )

    def close(self):
        self.db.close()

    def __repr__(self):
        params = (
            (p, getattr(self, p))
            for p in ('filepath', 'maxsize', 'ttl')
        )
        return (
            f"{self.__class__.__name__}"
            f"({', '.join(f'{k}={repr(v)}' for k,v in params)})"
        )

    def __enter__(self):
        self.init_db()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __setitem__(self, key, value):
        with self.db as db:
            db.execute(
                "INSERT OR REPLACE INTO cache VALUES "
                f"(?, {self.SQLITE_TIMESTAMP}, ?)",
                (key, value)
            )

    def __getitem__(self, key):
        res = self.get(key, None)
        if res is None:
            raise KeyError('Not found')
        else:
            return res

    def __delitem__(self, key):
        cursor = self.db.execute(self.sql_delete, (key,))
        if cursor.rowcount == 0:
            raise KeyError('Not found')

    def get(self, key, default=None):
        rows = self.db.execute(
            self.sql_select,
            (key,),
        ).fetchall()
        return rows[0][0] if rows else default

    def init_db(self):
        after_insert_actions = []
        if self.ttl > 0:
            after_insert_actions.append(
                '  DELETE FROM cache WHERE '
                f'({self.SQLITE_TIMESTAMP} - ts) > {self.ttl};'
            )
        if self.maxsize > 0:
            after_insert_actions.append(
                '  DELETE FROM cache WHERE key in ('
                'SELECT key FROM cache '
                'ORDER BY ts LIMIT '
                f'max(0, (SELECT COUNT(key) FROM cache) - {self.maxsize}));'
            )

        with self.db as db:
            db.execute(
                'CREATE TABLE IF NOT EXISTS cache ('
                ' key BINARY PRIMARY KEY,'
                ' ts REAL,'
                ' value BLOB'
                ') WITHOUT ROWID'
            )
            db.execute('CREATE INDEX IF NOT EXISTS i_cache_ts ON cache (ts)')
            if after_insert_actions:
                trigger_ddl = (
                    'CREATE TRIGGER IF NOT EXISTS t_cache_cleanup\n'
                    'AFTER INSERT ON cache FOR EACH ROW BEGIN\n'
                    '%s\n'
                    'END'
                ) % '\n'.join(after_insert_actions)
                db.execute(trigger_ddl)

    def clear(self):
        with self.db as db:
            db.execute('DROP TABLE IF EXISTS cache')
            db.execute('VACUUM')
        self.init_db()

    def items(self):
        cursor = self.db.execute('SELECT key, value FROM cache ORDER BY ts')
        try:
            yield from cursor
        finally:
            cursor.close()

    def remove(self):
        self.close()
        with suppress(FileNotFoundError):
            os.remove(self.filepath)
