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
                    module TEXT,
                    data JSONB
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


def save(command, target, module, data):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO results (command, target, module, data) VALUES (%s, %s, %s, %s)",
                (command, target, module, json.dumps(data, ensure_ascii=False)),
            )
            conn.commit()


def query(target=None, module=None, limit=50):
    sql = "SELECT ts, command, target, module, data FROM results WHERE 1=1"
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
    return [
        {"ts": str(r["ts"]), "command": r["command"], "target": r["target"],
         "module": r["module"], "data": r["data"]}
        for r in rows
    ]


def stats():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM results")
            total = cur.fetchone()[0]
            cur.execute("SELECT module, COUNT(*) FROM results GROUP BY module")
            by_module = dict(cur.fetchall())
    return {"total": total, "by_module": by_module}