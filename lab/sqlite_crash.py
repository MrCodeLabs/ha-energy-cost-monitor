"""Make a real hot SQLite journal with disposable lab data."""

from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys


def interrupt_write(path: Path, change: str) -> Path:
    """Exit mid-transaction after dirty pages have spilled into the DB."""
    program = """
import os
import sqlite3
import sys

db = sqlite3.connect(sys.argv[1], isolation_level=None)
db.execute("PRAGMA journal_mode=DELETE")
db.execute("PRAGMA synchronous=FULL")
db.execute("PRAGMA cache_size=4")
db.execute("BEGIN IMMEDIATE")
db.execute(sys.argv[2])
db.execute("CREATE TABLE uncommitted_crash_probe(body BLOB)")
db.executemany("INSERT INTO uncommitted_crash_probe VALUES (zeroblob(8192))", [()] * 32)
os._exit(0)
"""
    subprocess.run([sys.executable, "-c", program, str(path), change], check=True, timeout=15)
    journal = path.with_name(path.name + "-journal")
    assert journal.is_file()
    try:
        with closing(sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)) as db:
            db.execute("PRAGMA application_id").fetchone()
    except sqlite3.OperationalError as error:
        if error.sqlite_errorcode != sqlite3.SQLITE_READONLY_ROLLBACK:
            raise
    else:
        raise AssertionError("expected a hot journal that requires writable recovery")
    return journal
