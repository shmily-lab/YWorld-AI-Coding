# -*- coding: utf-8 -*-
"""数据库连接与 SQL 执行的底层工具。

设计要点：
1. isolation_level=None —— 走 autocommit，用户手写 BEGIN/COMMIT/ROLLBACK 才能生效，
   否则 Python 的隐式事务会把 BEGIN 变成嵌套事务，教学场景会讲不清楚。
2. 支持多语句（用于「建表 + 查询」或「UPDATE + 验证」这类题）。
3. 结果归一化：浮点四舍五入、行排序，使判分不受返回顺序影响。
"""
from __future__ import annotations

import os
import re
import shutil
import sqlite3
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX = os.path.join(ROOT, "sandbox")
TEMPLATE_DB = os.path.join(SANDBOX, "learn.db")
SESSION_DIR = os.path.join(SANDBOX, "sessions")
PROGRESS_FILE = os.path.join(ROOT, "progress", "progress.json")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)


def wipe_all_tables(path: str) -> None:
    """删干净库里的所有用户表/索引/视图/触发器。

    刻意不用「删除数据库文件再重建」的方式：受限沙箱会拦截文件删除。
    """
    if not os.path.exists(path):
        return
    con = sqlite3.connect(path, isolation_level=None)
    try:
        objs = con.execute(
            "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for kind, name in objs:
            con.execute(f"DROP {kind.upper()} IF EXISTS \"{name}\"")
        con.execute("VACUUM")
    finally:
        con.close()


def connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


# --------------------------------------------------------------------------
# 语句拆分：尊重字符串字面量 / 标识符引号 / 行注释 / 块注释
# --------------------------------------------------------------------------
def split_statements(sql: str) -> list[str]:
    stmts, buf = [], []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        if ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
            i += 1
            while i < n:
                buf.append(sql[i])
                if sql[i] == quote:
                    # SQL 中用两个连续引号表示字面量中的一个引号
                    if i + 1 < n and sql[i + 1] == quote:
                        buf.append(sql[i + 1])
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        if ch == "-" and sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j == -1 else j
            buf.append(sql[i:j])
            i = j
            continue
        if ch == "/" and sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            j = n if j == -1 else j + 2
            buf.append(sql[i:j])
            i = j
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                stmts.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        stmts.append(tail)
    return stmts


def strip_comments(sql: str) -> str:
    return re.sub(r"/\*.*?\*/", " ", re.sub(r"--[^\n]*", " ", sql), flags=re.S)


# --------------------------------------------------------------------------
# 结果归一化
# --------------------------------------------------------------------------
def _norm_value(v):
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, bytes):
        return repr(v)
    if v is None:
        return None
    return v


def _sort_key(row):
    keys = []
    for v in row:
        if v is None:
            keys.append((0, ""))
        elif isinstance(v, bool):
            keys.append((1, str(v)))
        elif isinstance(v, (int, float)):
            keys.append((2, f"{round(float(v), 6):.6f}"))
        elif isinstance(v, bytes):
            keys.append((3, repr(v)))
        else:
            keys.append((4, str(v)))
    return tuple(keys)


def normalize_rows(rows: list[sqlite3.Row]) -> list[tuple]:
    plain = [tuple(_norm_value(x) for x in r) for r in rows]
    # MySQL/SQLite 都不保证无序结果集的顺序，默认按内容排序再比较
    try:
        return sorted(plain, key=_sort_key)
    except Exception:
        return sorted(plain, key=lambda r: tuple(map(str, r)))


def rows_to_lists(rows: list[sqlite3.Row]) -> list[list]:
    return [[_norm_value(x) for x in r] for r in rows]


# --------------------------------------------------------------------------
# 执行
# --------------------------------------------------------------------------
MAX_ROWS = 2000


def execute(con: sqlite3.Connection, sql: str, max_rows: int = MAX_ROWS):
    """执行（可能多语句的）SQL，返回最后一个结果集。

    返回 dict: {columns, rows, rowcount, truncated, statements, error}
    """
    stmts = split_statements(sql)
    if not stmts:
        return {"columns": [], "rows": [], "rowcount": 0, "truncated": False,
                "statements": 0, "error": "空语句"}

    columns, rows, rowcount, truncated = [], [], 0, False
    try:
        for idx, st in enumerate(stmts):
            cur = con.execute(st)
            rowcount = cur.rowcount if cur.rowcount is not None else 0
            if cur.description:
                columns = [d[0] for d in cur.description]
                rows = cur.fetchmany(max_rows + 1)
                truncated = len(rows) > max_rows
                rows = rows[:max_rows]
            else:
                # 最后一条如果是 DML/DDL，结果集保持上一次 SELECT 的空集语义
                if idx == len(stmts) - 1:
                    columns, rows = [], []
    except Exception as exc:  # noqa: BLE001
        return {"columns": columns, "rows": rows, "rowcount": rowcount,
                "truncated": truncated, "statements": len(stmts),
                "error": f"{type(exc).__name__}: {exc}"}
    return {"columns": columns, "rows": rows, "rowcount": rowcount,
            "truncated": truncated, "statements": len(stmts), "error": None}


def fetchall(con: sqlite3.Connection, sql: str) -> list[tuple]:
    return [tuple(r) for r in con.execute(sql).fetchall()]


# --------------------------------------------------------------------------
# 数据库副本
# --------------------------------------------------------------------------
_TMP_ROOT = os.path.join(tempfile.gettempdir(), "dblab_attempts")
os.makedirs(_TMP_ROOT, exist_ok=True)


def fresh_copy(dest: str | None = None) -> str:
    """复制模板库，任何修改都不会污染题库基准数据。

    刻意**不使用 os.remove / mkstemp**：某些受限沙箱会拦截删除操作。
    这里改用「按线程复用的临时文件 + 覆盖写」：shutil.copyfile 截断重写，
    既不会堆积垃圾文件，也不会因清理失败而报错。
    """
    if dest is None:
        key = re.sub(r"\W", "_", threading.current_thread().name)
        dest = os.path.join(_TMP_ROOT, f"attempt_{os.getpid()}_{key}.db")
    if not os.path.exists(TEMPLATE_DB):
        raise FileNotFoundError(f"模板库不存在：{TEMPLATE_DB}，请先运行 `python run.py init`")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(TEMPLATE_DB, dest)
    return dest


def session_db(session_id: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_-]", "", session_id) or "default"
    path = os.path.join(SESSION_DIR, f"{safe}.db")
    if not os.path.exists(path):
        shutil.copyfile(TEMPLATE_DB, path)
    return path


def reset_session(session_id: str) -> str:
    path = session_db(session_id)
    shutil.copyfile(TEMPLATE_DB, path)
    return path


def schema_info(con: sqlite3.Connection) -> dict:
    """返回 {表名: [列信息...]}，用于前端 Schema 浏览器。"""
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    out = {}
    for t in tables:
        cols = []
        for r in con.execute(f"PRAGMA table_info({t})"):
            cols.append({"name": r[1], "type": r[2], "notnull": bool(r[3]),
                         "default": r[4], "pk": bool(r[5])})
        cnt = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        out[t] = {"columns": cols, "rows": cnt}
    return out
