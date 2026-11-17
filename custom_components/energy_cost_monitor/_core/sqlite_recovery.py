"""Recover interrupted writes to integration-owned SQLite stores at startup."""

from contextlib import closing
from pathlib import Path
import sqlite3


def recover_interrupted_write(path: Path, application_id: int) -> None:
    """Let SQLite replay its own hot journal before normal read-only validation."""
    if not path.with_name(path.name + "-journal").is_file():
        return
    uri = path.absolute().as_uri()
    try:
        with closing(sqlite3.connect(uri + "?mode=ro", uri=True, timeout=15)) as db:
            db.execute("PRAGMA application_id").fetchone()
        return
    except sqlite3.DatabaseError as error:
        if getattr(error, "sqlite_errorcode", None) != sqlite3.SQLITE_READONLY_ROLLBACK:
            # The normal store validator handles other failures.
            return

    # A hot journal prevents even a read-only PRAGMA. Check the application's
    # header before allowing SQLite to write to this file.
    with path.open("rb") as stream:
        header = stream.read(72)
    if (len(header) != 72 or not header.startswith(b"SQLite format 3\0")
            or int.from_bytes(header[68:72], "big") != application_id):
        raise ValueError("unsupported_database")

    # mode=rw refuses to create a missing file. The first read obtains
    # SQLite's locks and triggers recovery; it does not start an app write.
    with closing(sqlite3.connect(uri + "?mode=rw", uri=True, timeout=15)) as db:
        if db.execute("PRAGMA application_id").fetchone()[0] != application_id:
            raise ValueError("unsupported_database")
