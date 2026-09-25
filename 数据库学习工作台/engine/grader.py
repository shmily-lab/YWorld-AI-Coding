# -*- coding: utf-8 -*-
"""判分引擎：把一道题的判分规则套到用户提交的 SQL 上。

三种判分模式（题目里用 verify["mode"] 指定）：

1. exact  结果集比对
       verify = {"mode": "exact", "answer": "<标准答案 SQL>"}
       把标准答案和用户答案各跑一遍，按「内容排序后的行多重集」比对。
       不受返回顺序影响；浮点按 6 位小数归一。

2. check  自定义校验 SQL
       verify = {"mode": "check", "check": "<返回一行的校验 SQL>", "answer": "<可选，用于展示参考>"}
       先执行用户 SQL（可能是 INSERT/UPDATE/DDL），再跑校验 SQL。
       取第一行第一列：字符串以 PASS 开头（或为 OK/TRUE）→ 通过；数值等于 1 → 通过；
       否则整段文本当作失败原因返回。因此建议校验 SQL 写成：
           SELECT CASE WHEN <条件> THEN 'PASS' ELSE 'FAIL: 期望 5 行，实际 ' || N END

3. plan  执行计划断言
       verify = {"mode": "plan", "answer": "...",
                 "contains": ["USING INDEX"], "not_contains": ["SCAN products"]}
       适合阶段 8「必须走索引」类题目。断言对最后一条 SELECT 的
       EXPLAIN QUERY PLAN 输出做子串匹配（忽略大小写）。
"""
from __future__ import annotations

import os
import sqlite3

from . import db

_TRUTHY = {"PASS", "OK", "TRUE", "1", "Y", "YES"}


def _result_dict(ok: bool, mode: str, message: str, **kw) -> dict:
    out = {"ok": ok, "mode": mode, "message": message}
    out.update(kw)
    return out


def grade(question: dict, user_sql: str) -> dict:
    mode = question["verify"].get("mode", "exact")
    work = db.fresh_copy()
    try:
        con = db.connect(work)
        try:
            if mode == "exact":
                return _grade_exact(con, question, user_sql)
            if mode == "check":
                return _grade_check(con, question, user_sql)
            if mode == "plan":
                return _grade_plan(con, question, user_sql)
            return _result_dict(False, mode, f"未知的判分模式：{mode}")
        finally:
            con.close()
    finally:
        try:
            os.remove(work)
        except OSError:
            pass


# ------------------------------------------------------------------ 通用执行
def _hint_for_error(msg: str) -> str:
    """把常见报错翻译成人话，顺带纠正一个习惯。"""
    low = msg.lower()
    if "ambiguous column name" in low:
        col = msg.split(":")[-1].strip()
        return (f"SQL 执行失败：{msg}\n"
                f"  提示：多表查询里 {col} 不止一张表有，必须写成 表别名.{col}（例如 o.{col}）。\n"
                f"  给所有列加前缀限定是好习惯，也能避免以后有人加字段导致这条 SQL 突然报错。")
    if "no such column" in low:
        return f"SQL 执行失败：{msg}\n  提示：列名或表别名写错了，可用 Schema 浏览器核对。"
    if "more than one row" in low:
        return (f"SQL 执行失败：{msg}\n"
                f"  提示：这是标量子查询返回了多行。改用 IN / EXISTS，或加 LIMIT 1 / 聚合函数。")
    return f"SQL 执行失败：{msg}"


def _run(con: sqlite3.Connection, sql: str, label: str):
    res = db.execute(con, sql)
    if res["error"]:
        return None, res
    return res, None


# ------------------------------------------------------------------ exact
def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _close(a, b, tol_scale: float = 1.0) -> bool:
    """数值容差比较。

    同一个聚合在不同写法下末位会有差异（例如 SUM(x) 得 710595.600000012，
    而 ROUND(SUM(x),2) 得 710595.6），这属于浮点表示误差而非答案错误，
    因此允许：|a-b| <= max(0.005 * tol_scale, |a| * 1e-9)
    """
    if _num(a) and _num(b):
        if abs(a - b) <= 0.005 * tol_scale:
            return True
        return abs(a - b) <= abs(a) * 1e-9 * tol_scale
    return a == b


def _row_eq(a: tuple, b: tuple, tol: float) -> bool:
    if len(a) != len(b):
        return False
    return all(_close(x, y, tol) for x, y in zip(a, b))


def _diff(exp_rows: list[tuple], usr_rows: list[tuple], tol: float):
    """带容差的多重集差分：找出缺的行与多的行。"""
    missing, extra = [], list(usr_rows)
    detail = len(exp_rows) <= 800
    for e in exp_rows:
        hit = -1
        for i, u in enumerate(extra):
            if _row_eq(e, u, tol):
                hit = i
                break
        if hit >= 0:
            extra.pop(hit)
        elif detail:
            missing.append(e)
    if not detail:
        missing = []
        extra = []
    return missing, extra


def _grade_exact(con, question: dict, user_sql: str) -> dict:
    answer = question["verify"]["answer"]
    check_cols = question["verify"].get("check_columns", False)
    tol = float(question["verify"].get("tol", 1.0))

    exp = db.execute(con, answer)
    # 参考答案本身有错 => 题库 BUG，直接暴露出来而不是判用户错
    if exp["error"]:
        return _result_dict(False, "exact", f"【题库错误】参考答案无法执行：{exp['error']}")

    user = db.execute(con, user_sql)
    if user["error"]:
        return _result_dict(False, "exact", _hint_for_error(user["error"]))

    exp_rows = db.normalize_rows(exp["rows"])
    usr_rows = db.normalize_rows(user["rows"])

    missing, extra = _diff(exp_rows, usr_rows, tol)
    problems = []
    if len(usr_rows) != len(exp_rows):
        problems.append(f"行数不符：期望 {len(exp_rows)} 行，实际 {len(usr_rows)} 行")
    if missing:
        problems.append(f"缺失 {len(missing)} 行")
    if extra:
        problems.append(f"多出 {len(extra)} 行")
    if not problems and len(usr_rows) == len(exp_rows) and len(usr_rows) <= 800:
        # 行数一致但配对失败时（例如某列值差一点），给具体行
        for e, u in zip(exp_rows, usr_rows):
            if not _row_eq(e, u, tol):
                problems.append(f"第 {exp_rows.index(e) + 1} 行不符")
                break

    if check_cols and exp["columns"] and exp["columns"] != user["columns"]:
        problems.append(f"列名不符：期望 {exp['columns']}，实际 {user['columns']}")

    ok = not problems
    return _result_dict(
        ok, "exact",
        "通过 ✅ 结果集与标准答案完全一致" if ok else "；".join(problems),
        columns=user["columns"],
        rows=db.rows_to_lists(user["rows"]),
        truncated=user["truncated"],
        expected_columns=exp["columns"],
        expected_rows=db.rows_to_lists(exp["rows"]),
        diff={"missing": [list(r) for r in missing[:5]], "extra": [list(r) for r in extra[:5]]},
    )


# ------------------------------------------------------------------ check
def _grade_check(con, question: dict, user_sql: str) -> dict:
    user = db.execute(con, user_sql)
    if user["error"]:
        return _result_dict(False, "check", f"SQL 执行失败：{user['error']}")

    # 挂载未被修改的基准库，校验 SQL 里可以用 base.xxx 对比原始状态
    base_path = db.TEMPLATE_DB.replace("'", "''")
    try:
        con.execute(f"ATTACH '{base_path}' AS base")
    except Exception as exc:  # noqa: BLE001
        return _result_dict(False, "check", f"【题库错误】无法挂载基准库：{exc}")

    chk_sql = question["verify"]["check"]
    row = None
    try:
        for st in db.split_statements(chk_sql):
            cur = con.execute(st)
            if cur.description:
                row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        return _result_dict(False, "check", f"【题库错误】校验 SQL 无法执行：{type(exc).__name__}: {exc}")

    if row is None:
        return _result_dict(False, "check", "校验 SQL 没有返回任何行，无法判定")

    val = row[0]
    msg = str(val)
    if isinstance(val, str):
        ok = val.strip().upper() in _TRUTHY or val.strip().upper().startswith("PASS")
    elif isinstance(val, (int, float)) and not isinstance(val, bool):
        ok = val == 1
    else:
        ok = bool(val)
    if ok and not msg.upper().startswith("PASS"):
        msg = f"通过 ✅（校验返回 {msg}）"
    return _result_dict(
        ok, "check", msg,
        columns=user["columns"],
        rows=db.rows_to_lists(user["rows"]),
        truncated=user["truncated"],
        expected_columns=[],
        expected_rows=[],
        diff={"missing": [], "extra": []},
    )


# ------------------------------------------------------------------ plan
def _explain(con, sql: str) -> tuple[list[str], str]:
    stmts = db.split_statements(sql)
    target = None
    for s in stmts:
        u = s.upper()
        if u.strip().startswith("SELECT") or u.strip().startswith("WITH"):
            target = s
    if target is None:
        target = stmts[-1] if stmts else sql
    cur = con.execute(f"EXPLAIN QUERY PLAN {target}")
    cols = [d[0] for d in cur.description]
    detail_idx = cols.index("detail") if "detail" in cols else len(cols) - 1
    lines = [r[detail_idx] for r in cur.fetchall()]
    return lines, "\n".join(lines)


def _grade_plan(con, question: dict, user_sql: str) -> dict:
    user = db.execute(con, user_sql)
    if user["error"]:
        return _result_dict(False, "plan", f"SQL 执行失败：{user['error']}")

    try:
        lines, text = _explain(con, user_sql)
    except Exception as exc:  # noqa: BLE001
        return _result_dict(False, "plan", f"EXPLAIN 执行失败：{type(exc).__name__}: {exc}")

    low = text.lower()
    problems = []
    for token in question["verify"].get("contains", []):
        if token.lower() not in low:
            problems.append(f"执行计划中缺少「{token}」")
    for token in question["verify"].get("not_contains", []):
        if token.lower() in low:
            problems.append(f"执行计划中不应出现「{token}」")

    exp_ans = question["verify"].get("answer")
    exp_rows, exp_cols = [], []
    if exp_ans and question["verify"].get("compare_result", False):
        exp = db.execute(db.connect(db.TEMPLATE_DB), exp_ans)
        exp_rows = db.rows_to_lists(exp["rows"])
        exp_cols = exp["columns"]

    ok = not problems
    return _result_dict(
        ok, "plan",
        "通过 ✅ 执行计划满足断言" if ok else "；".join(problems),
        columns=["QUERY PLAN"],
        rows=[[l] for l in lines],
        truncated=False,
        expected_columns=exp_cols,
        expected_rows=exp_rows,
        plan=lines,
        diff={"missing": [], "extra": []},
    )


# ------------------------------------------------------------------ 自检
def selfcheck_report(questions: list[dict]) -> list[tuple[str, bool, str]]:
    """对题库做自检：每道题的参考答案必须能通过自己的判分规则。"""
    report = []
    for q in questions:
        v = q["verify"]
        sql = v.get("answer")
        if v.get("mode") == "check":
            sql = sql or v.get("check")
        if not sql:
            report.append((q["id"], False, "缺少 answer"))
            continue
        r = grade(q, sql)
        report.append((q["id"], bool(r["ok"]), r["message"]))
    return report
