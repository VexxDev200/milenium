import csv
import os
import sqlite3
from pathlib import Path
from milenium.modules.logger import progress


SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT,
    name TEXT,
    email TEXT,
    username TEXT,
    mobile_phone TEXT,
    location TEXT,
    birthday TEXT,
    gender TEXT
);
CREATE INDEX IF NOT EXISTS idx_uid ON records(uid);
CREATE INDEX IF NOT EXISTS idx_email ON records(email);
CREATE INDEX IF NOT EXISTS idx_username ON records(username);
CREATE INDEX IF NOT EXISTS idx_phone ON records(mobile_phone);
"""

FTS_SETUP = """
CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(
    name, email, username, location,
    content='records',
    content_rowid='id'
);
"""


def db_path(csv_path):
    p = Path(csv_path)
    return p.with_suffix(".milenium.sqlite")


def _has_fts5(conn):
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_test USING fts5(a);")
        conn.execute("DROP TABLE IF EXISTS _fts5_test;")
        return True
    except Exception:
        return False


def init_db(csv_path, force=False):
    csv_path = os.path.abspath(csv_path)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)

    out = db_path(csv_path)
    exists = out.exists()
    if exists and not force:
        progress(f"CSV DB уже существует: {out}")
        return str(out)

    progress(f"CSV → SQLite: {csv_path}")
    conn = sqlite3.connect(str(out))
    try:
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM records")
        if _has_fts5(conn):
            conn.execute("DROP TABLE IF EXISTS records_fts")

        with open(csv_path, "r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            batch = []
            total = 0
            for row in reader:
                batch.append((
                    (row.get("uid") or "").strip(),
                    (row.get("name") or "").strip(),
                    (row.get("email") or "").strip(),
                    (row.get("username") or "").strip(),
                    (row.get("mobile_phone") or "").strip(),
                    (row.get("location") or "").strip(),
                    (row.get("birthday") or "").strip(),
                    (row.get("gender") or "").strip(),
                ))
                if len(batch) >= 5000:
                    conn.executemany(
                        "INSERT INTO records (uid, name, email, username, mobile_phone, location, birthday, gender) VALUES (?,?,?,?,?,?,?,?)",
                        batch,
                    )
                    total += len(batch)
                    progress(f"CSV импорт: {total} строк")
                    batch.clear()
            if batch:
                conn.executemany(
                    "INSERT INTO records (uid, name, email, username, mobile_phone, location, birthday, gender) VALUES (?,?,?,?,?,?,?,?)",
                    batch,
                )
                total += len(batch)
                progress(f"CSV импорт: {total} строк")

        conn.commit()

        if _has_fts5(conn):
            conn.executescript(FTS_SETUP)
            conn.execute("INSERT INTO records_fts(records_fts) VALUES ('rebuild')")
            conn.commit()
            progress("FTS5 индекс построен")
        else:
            progress("FTS5 недоступен — используются обычные индексы")
    finally:
        conn.close()

    progress(f"Готово: {total} строк → {out}")
    return str(out)


def _connect(csv_path):
    out = db_path(csv_path)
    if not out.exists():
        init_db(csv_path)
    conn = sqlite3.connect(str(out))
    conn.row_factory = sqlite3.Row
    return conn


def search(csv_path, query, limit=20):
    conn = _connect(csv_path)
    try:
        q = query.strip()
        rows = []
        # FTS5 быстрый текстовый поиск
        try:
            cur = conn.execute(
                """SELECT r.* FROM records_fts fts
                   JOIN records r ON r.id = fts.rowid
                   WHERE records_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (q, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            rows = []

        if not rows:
            like = f"%{q}%"
            cur = conn.execute(
                """SELECT * FROM records
                   WHERE uid LIKE ? OR name LIKE ? OR email LIKE ? OR username LIKE ?
                      OR mobile_phone LIKE ? OR location LIKE ?
                   LIMIT ?""",
                (like, like, like, like, like, like, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


def exact(csv_path, field, value, limit=20):
    allowed = {"uid", "name", "email", "username", "mobile_phone", "location", "birthday", "gender"}
    if field not in allowed:
        raise ValueError(f"Недопустимое поле: {field}. Доступны: {', '.join(sorted(allowed))}")

    conn = _connect(csv_path)
    try:
        cur = conn.execute(
            f"SELECT * FROM records WHERE {field} = ? LIMIT ?",
            (value, limit),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def stats(csv_path):
    conn = _connect(csv_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        has_fts = False
        try:
            conn.execute("SELECT 1 FROM records_fts LIMIT 1")
            has_fts = True
        except Exception:
            pass
        return {
            "csv": csv_path,
            "db": str(db_path(csv_path)),
            "rows": total,
            "fts5": has_fts,
        }
    finally:
        conn.close()
