# -*- coding: utf-8 -*-
"""学习进度持久化（含错题集、笔记、标记、复习排期）。

progress/progress.json 是纯文本 JSON，可直接查看与版本管理。

结构（version 2）：
{
  "version": 2,
  "questions": {
    "S3-Q03": {
      "attempts": 3, "passed": true, "first_pass": "...", "last_at": "...",
      "last_sql": "...", "last_ok": true,
      "review_level": 2, "next_review": "2026-09-27",
      "history": [{"at": "...", "ok": false, "sql": "...", "message": "..."}],
      "mistakes": [{"at": "...", "sql": "...", "message": "..."}],
      "solved": false,                  # 错题本里的题是否已攻克
      "note": "", "mark": "",           # mark: star / flag / done
      "highlights": [{"text": "...", "note": "...", "at": "..."}]
    }
  }
}
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from .db import PROGRESS_FILE

VERSION = 2


def _empty() -> dict:
    return {
        "attempts": 0, "passed": False, "first_pass": None,
        "last_at": None, "last_sql": "", "last_ok": None,
        "review_level": 0, "next_review": None,
        "history": [], "mistakes": [],
        "solved": False, "note": "", "mark": "", "highlights": [],
    }


def _migrate(raw: dict) -> dict:
    """把 v1（{qid: {...}} 平铺）升级成 v2。"""
    if raw.get("version") == VERSION and isinstance(raw.get("questions"), dict):
        return raw
    qs = {}
    for k, v in raw.items():
        if k == "version" or not isinstance(v, dict):
            continue
        ent = _empty()
        ent.update(v)
        ent.setdefault("history", [])
        ent.setdefault("mistakes", [])
        ent.setdefault("highlights", [])
        qs[k] = ent
    return {"version": VERSION, "questions": qs}


def load() -> dict:
    """返回 {qid: 题目学习记录} 的扁平字典（对外接口保持不变）。"""
    if not os.path.exists(PROGRESS_FILE):
        return {}
    try:
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError:
        return {}
    return _migrate(raw).get("questions", {})


def save(data: dict) -> None:
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"version": VERSION, "questions": data}, f, ensure_ascii=False, indent=2)


def get(qid: str) -> dict:
    return load().get(qid, _empty())


def record(qid: str, ok: bool, sql: str = "", message: str = "") -> dict:
    """记录一次提交：累计次数、历史、错题、复习排期。"""
    from .review import schedule_review  # 延迟导入，避免循环依赖

    data = load()
    ent = data.get(qid, _empty())
    now = datetime.now()

    ent["attempts"] = ent.get("attempts", 0) + 1
    ent["last_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
    ent["last_sql"] = sql
    ent["last_ok"] = ok
    ent.setdefault("history", []).append({
        "at": ent["last_at"], "ok": ok, "sql": sql, "message": message,
    })
    ent["history"] = ent["history"][-50:]          # 只保留最近 50 条

    if ok:
        ent["passed"] = True
        if not ent.get("first_pass"):
            ent["first_pass"] = ent["last_at"]
        ent["solved"] = True                        # 做过错 → 现在攻克了
    else:
        ent.setdefault("mistakes", []).append({
            "at": ent["last_at"], "sql": sql, "message": message,
        })
        ent["mistakes"] = ent["mistakes"][-20:]

    schedule_review(ent, ok, now)
    data[qid] = ent
    save(data)
    return ent


def set_note(qid: str, text: str) -> dict:
    data = load()
    ent = data.get(qid, _empty())
    ent["note"] = text
    data[qid] = ent
    save(data)
    return ent


def set_mark(qid: str, mark: str) -> dict:
    """mark: star（收藏）/ flag（易错，重点复习）/ done（自认已掌握）/ ''（清除）"""
    data = load()
    ent = data.get(qid, _empty())
    ent["mark"] = mark if mark in ("star", "flag", "done", "") else ""
    data[qid] = ent
    save(data)
    return ent


def add_highlight(qid: str, text: str, note: str = "") -> dict:
    """标记笔：把题面/讲解里选中的一段话存下来，附一句自己的批注。"""
    data = load()
    ent = data.get(qid, _empty())
    ent.setdefault("highlights", []).append({
        "text": text, "note": note,
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    data[qid] = ent
    save(data)
    return ent


def clear_highlights(qid: str) -> dict:
    data = load()
    ent = data.get(qid, _empty())
    ent["highlights"] = []
    data[qid] = ent
    save(data)
    return ent


def reset_question(qid: str, hard: bool = False) -> dict:
    """重做某道题。

    hard=False（默认）：只清答题记录（次数 / 通过 / 错题 / 复习排期），
        **保留**笔记、标记和划重点 —— 「隔段时间重做一遍」时不该把笔记也弄丢。
    hard=True：连笔记标记一起清。
    """
    data = load()
    old = data.get(qid, _empty())
    ent = _empty()
    if not hard:
        ent["note"] = old.get("note", "")
        ent["mark"] = old.get("mark", "")
        ent["highlights"] = old.get("highlights", [])
    data[qid] = ent
    save(data)
    return ent


def reset_many(qids: list[str], hard: bool = False) -> int:
    data = load()
    for qid in qids:
        old = data.get(qid, _empty())
        ent = _empty()
        if not hard:
            ent["note"] = old.get("note", "")
            ent["mark"] = old.get("mark", "")
            ent["highlights"] = old.get("highlights", [])
        data[qid] = ent
    save(data)
    return len(qids)


def backup() -> str | None:
    """清空进度前留一份备份到 progress/progress.backup.json。"""
    import shutil
    if not os.path.exists(PROGRESS_FILE):
        return None
    dst = os.path.join(os.path.dirname(PROGRESS_FILE), "progress.backup.json")
    shutil.copyfile(PROGRESS_FILE, dst)
    return dst


def clear_all(hard: bool = True) -> int:
    """清空全部学习记录。调用方应先 backup()。"""
    data = load()
    n = len(data)
    if hard:
        save({})
        return n
    for qid in list(data):
        keep = {k: data[qid].get(k) for k in ("note", "mark", "highlights")}
        ent = _empty()
        ent.update(keep)
        data[qid] = ent
    save(data)
    return n


def notes_markdown(questions: list[dict]) -> str:
    """导出全部笔记、标记与划重点，成一个 Markdown 文档。"""
    data = load()
    lines = ["# 学习笔记与标记\n"]
    n = 0
    for q in questions:
        d = data.get(q["id"])
        if not d:
            continue
        mark, note, hl = d.get("mark", ""), d.get("note", ""), d.get("highlights") or []
        if not (mark or note or hl):
            continue
        n += 1
        mk = {"star": "⭐ 收藏", "flag": "❗ 易错", "done": "✓ 已掌握"}.get(mark, "")
        lines.append(f"\n## {q['id']} {q['title']} {mk}\n")
        if note:
            lines.append(f"**笔记**：{note}\n")
        if hl:
            lines.append("\n**划重点**：\n")
            for h in hl:
                lines.append(f"- {h['text']}"
                             + (f"  —— {h['note']}" if h.get("note") else "") + "\n")
    if n == 0:
        return "还没有任何笔记或标记。"
    return "".join(lines)


def summary(questions: list[dict]) -> dict:
    data = load()
    by_stage: dict[int, dict] = {}
    for q in questions:
        st = q["stage"]
        box = by_stage.setdefault(st, {"total": 0, "passed": 0, "points": 0, "earned": 0})
        box["total"] += 1
        box["points"] += q.get("points", 0)
        d = data.get(q["id"])
        if d and d.get("passed"):
            box["passed"] += 1
            box["earned"] += q.get("points", 0)
    passed = [q for q in questions if (data.get(q["id"]) or {}).get("passed")]
    total = {
        "total": len(questions),
        "passed": len(passed),
        "points": sum(q.get("points", 0) for q in questions),
        "earned": sum(q.get("points", 0) for q in passed),
        "attempts": sum((data.get(q["id"]) or {}).get("attempts", 0) for q in questions),
    }
    wrong = [q["id"] for q in questions
             if ((data.get(q["id"]) or {}).get("mistakes") and
                 not (data.get(q["id"]) or {}).get("solved"))]
    return {"total": total, "stages": by_stage, "wrong": wrong,
            "wrong_cnt": len(wrong)}
