import os
import json
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_JNAjnTaz0UK5@ep-twilight-bar-b1ofdyot-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")


def _conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id SERIAL PRIMARY KEY,
                    ts TIMESTAMP DEFAULT NOW(),
                    command TEXT,
                    target TEXT,
                    target_type TEXT,
                    module TEXT,
                    found_count INTEGER DEFAULT 0,
                    data JSONB
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id SERIAL PRIMARY KEY,
                    ts TIMESTAMP DEFAULT NOW(),
                    target TEXT,
                    source TEXT,
                    url TEXT,
                    found BOOLEAN,
                    meta JSONB
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leaks (
                    id SERIAL PRIMARY KEY,
                    ts TIMESTAMP DEFAULT NOW(),
                    target TEXT,
                    email TEXT,
                    password TEXT,
                    source TEXT,
                    breach TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    ts TIMESTAMP DEFAULT NOW(),
                    queries INTEGER,
                    results INTEGER
                )
            """)
            conn.commit()


def save(command, target, module, data, target_type=None):
    found_count = 0
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and v.get("found"):
                found_count += 1

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO results (command, target, target_type, module, found_count, data)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (command, target, target_type, module, found_count,
                 json.dumps(data, ensure_ascii=False, default=str))
            )

            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, dict) and "url" in val:
                        cur.execute(
                            """INSERT INTO findings (target, source, url, found, meta)
                               VALUES (%s, %s, %s, %s, %s)""",
                            (target, key, val.get("url"), val.get("found", False),
                             json.dumps(val, ensure_ascii=False, default=str))
                        )
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict) and "url" in item:
                                cur.execute(
                                    """INSERT INTO findings (target, source, url, found, meta)
                                       VALUES (%s, %s, %s, %s, %s)""",
                                    (target, key, item.get("url"), True,
                                     json.dumps(item, ensure_ascii=False, default=str))
                                )
                            elif isinstance(item, str) and item.startswith("http"):
                                cur.execute(
                                    """INSERT INTO findings (target, source, url, found, meta)
                                       VALUES (%s, %s, %s, %s, %s)""",
                                    (target, key, item, True, json.dumps({"url": item}))
                                )

            if isinstance(data, dict) and "breaches" in data:
                for b in data.get("breaches", []):
                    cur.execute(
                        """INSERT INTO leaks (target, email, source, breach)
                           VALUES (%s, %s, %s, %s)""",
                        (target, target, "hibp", str(b))
                    )

            conn.commit()


def query(target=None, module=None, limit=50):
    sql = "SELECT ts, command, target, target_type, module, found_count, data FROM results WHERE 1=1"
    params = []
    if target:
        sql += " AND target LIKE %s"
        params.append(f"%{target}%")
    if module:
        sql += " AND module = %s"
        params.append(module)
    sql += " ORDER BY id DESC LIMIT %s"
    params.append(limit)
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def findings(target=None, limit=100):
    sql = "SELECT ts, target, source, url, found FROM findings WHERE 1=1"
    params = []
    if target:
        sql += " AND target LIKE %s"
        params.append(f"%{target}%")
    sql += " ORDER BY id DESC LIMIT %s"
    params.append(limit)
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def leaks(target=None, limit=100):
    sql = "SELECT ts, target, email, password, source, breach FROM leaks WHERE 1=1"
    params = []
    if target:
        sql += " AND target LIKE %s"
        params.append(f"%{target}%")
    sql += " ORDER BY id DESC LIMIT %s"
    params.append(limit)
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def stats():
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM results")
                total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM findings WHERE found = TRUE")
                findings_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM leaks")
                leaks_count = cur.fetchone()[0]
                cur.execute("SELECT module, COUNT(*) FROM results GROUP BY module")
                by_module = dict(cur.fetchall())
        return {
            "total": total,
            "findings": findings_count,
            "leaks": leaks_count,
            "by_module": by_module,
        }
    except Exception as e:
        return {"total": 0, "findings": 0, "leaks": 0, "by_module": {}, "error": str(e)}