# -*- coding: utf-8 -*-
"""复习排期、错题调度与薄弱点诊断。

三件事：
1. 间隔复习（艾宾浩斯衰减曲线）：答对拉长间隔，答错立刻回到短间隔。
2. 融合题解锁：某个阶段全部做对之后，解锁一道「必须综合前 N 阶段」的融合题。
3. 薄弱点诊断：按知识点标签统计掌握度，输出「先补哪一块」的训练建议。
"""
from __future__ import annotations

from datetime import datetime, timedelta

# 答对后逐级拉长的复习间隔（天）
INTERVALS = [1, 2, 4, 7, 15, 30, 60]
MAX_LEVEL = len(INTERVALS) - 1


def _today() -> datetime:
    return datetime.now()


# ------------------------------------------------------------------ 1. 排期
def schedule_review(ent: dict, ok: bool, now: datetime | None = None) -> None:
    """就地更新一条学习记录的复习排期。"""
    now = now or _today()
    level = int(ent.get("review_level") or 0)
    if ok:
        level = min(level + 1, MAX_LEVEL)
    else:
        # 答错：退一级，并强制明天重做（错题不过夜）
        level = max(0, level - 1)
    ent["review_level"] = level
    days = INTERVALS[level] if ok else 1
    ent["next_review"] = (now + timedelta(days=days)).strftime("%Y-%m-%d")


def due_today(questions: list[dict], today: datetime | None = None) -> list[dict]:
    """返回今天该复习的题目，按紧急程度排序。

    优先级：未攻克的错题 > 手动标记为「易错」 > 到期的间隔复习 > 已解锁的融合题
    """
    from . import progress

    today = today or _today()
    tstr = today.strftime("%Y-%m-%d")
    data = progress.load()
    out = []

    for q in questions:
        d = data.get(q["id"]) or {}
        reason, prio = None, 99

        if d.get("mistakes") and not d.get("solved"):
            reason, prio = "错题未攻克", 0
        elif d.get("mark") == "flag":
            reason, prio = "已标记易错", 1
        elif d.get("passed") and (d.get("next_review") or "") <= tstr:
            reason, prio = "间隔复习到期", 2
        elif q.get("kind") == "review" and not d.get("passed") and review_unlocked(q, questions, data):
            reason, prio = "融合题已解锁", 3

        if reason:
            out.append({
                "id": q["id"], "title": q["title"], "stage": q["stage"],
                "reason": reason, "prio": prio,
                "attempts": d.get("attempts", 0),
                "next_review": d.get("next_review"),
                "tags": q.get("tags", []),
                "requires": q.get("requires", []),
            })

    out.sort(key=lambda x: (x["prio"], x["stage"], x["id"]))
    return out


def review_unlocked(q: dict, questions: list[dict], data: dict) -> bool:
    """融合题的前置阶段是否全部通过。"""
    need = q.get("requires") or []
    if not need:
        return True
    for st in need:
        stage_qs = [x for x in questions if x["stage"] == st and x.get("kind") != "review"]
        if not stage_qs:
            continue
        if not all((data.get(x["id"]) or {}).get("passed") for x in stage_qs):
            return False
    return True


# ------------------------------------------------------------------ 2. 诊断
def _question_quality(d: dict) -> float | None:
    """单题掌握度：0~1。没做过的返回 None。"""
    if not d:
        return None
    attempts = int(d.get("attempts") or 0)
    if attempts == 0:
        return None
    if d.get("passed"):
        # 一次过 = 满分；每多错一次扣 0.2，最低 0.4
        return max(0.4, 1.0 - 0.2 * (attempts - 1))
    # 一次都没答对：按错过的次数递减，说明卡得越久越该优先补
    return max(0.0, 0.3 - 0.1 * (attempts - 1))


def diagnose(questions: list[dict], data: dict | None = None) -> dict:
    """按知识点标签统计掌握度，给出训练建议。"""
    from . import progress

    data = data if data is not None else progress.load()
    from .loader import tag_stage
    TAG_STAGE = tag_stage()

    tag_stats: dict[str, dict] = {}
    for q in questions:
        d = data.get(q["id"]) or {}
        quality = _question_quality(d)
        for tag in (q.get("tags") or []):
            box = tag_stats.setdefault(tag, {
                "tag": tag, "stage": TAG_STAGE.get(tag, q["stage"]),
                "qids": [], "attempted": 0, "passed": 0,
                "quality_sum": 0.0, "quality_n": 0, "mistakes": 0,
            })
            box["qids"].append(q["id"])
            if d.get("attempts"):
                box["attempted"] += 1
                box["quality_sum"] += quality
                box["quality_n"] += 1
            if d.get("passed"):
                box["passed"] += 1
            box["mistakes"] += len(d.get("mistakes") or [])

    for box in tag_stats.values():
        box["quality"] = round(box["quality_sum"] / box["quality_n"], 3) if box["quality_n"] else None
        box["total"] = len(box["qids"])
        del box["quality_sum"], box["quality_n"]

    def classify(box):
        if box["quality"] is None:
            return "未练习"
        if box["quality"] >= 0.8:
            return "掌握"
        if box["quality"] >= 0.5:
            return "一般"
        return "薄弱"

    for box in tag_stats.values():
        box["level"] = classify(box)

    rows = sorted(tag_stats.values(),
                  key=lambda b: (b["quality"] is None,
                                 b["quality"] if b["quality"] is not None else 9,
                                 -b["mistakes"]))
    weak = [b for b in rows if b["level"] == "薄弱"]
    mid = [b for b in rows if b["level"] == "一般"]

    # 训练建议：优先补「练过但没掌握」的，其次才是完全没碰过的
    focus = (weak + mid)[:4]
    plan = []
    for box in focus:
        qids = [qid for qid in box["qids"] if not (data.get(qid) or {}).get("passed")]
        qids = qids or box["qids"]
        plan.append({
            "tag": box["tag"],
            "stage": box["stage"],
            "level": box["level"],
            "quality": box["quality"],
            "reason": _reason_for(box),
            "drill": qids[:3],
        })

    attempted = [q for q in questions if (data.get(q["id"]) or {}).get("attempts")]
    first_try = [q for q in attempted
                 if (data.get(q["id"]) or {}).get("attempts") == 1
                 and (data.get(q["id"]) or {}).get("passed")]
    overall = {
        "attempted": len(attempted),
        "passed": len([q for q in questions if (data.get(q["id"]) or {}).get("passed")]),
        "avg_attempts": round(sum((data.get(q["id"]) or {}).get("attempts", 0)
                                  for q in attempted) / len(attempted), 2) if attempted else 0,
        "first_try_rate": round(len(first_try) / len(attempted) * 100, 1) if attempted else 0,
    }
    return {"tags": rows, "focus": plan, "overall": overall,
            "weak_cnt": len(weak), "mid_cnt": len(mid)}


def _reason_for(box: dict) -> str:
    if box["quality"] is None:
        return "还没练过，建议先做两道建立手感"
    if box["quality"] < 0.5:
        return f"练了 {box['attempted']} 道、错了 {box['mistakes']} 次，正确率明显偏低，是当前的短板"
    return f"能做对但不够稳（正确率 {int(box['quality'] * 100)}%），再练两道巩固一下"


# ------------------------------------------------------------------ 3. 错题
def wrong_set(questions: list[dict]) -> list[dict]:
    """未攻克的错题（含最近一次的错误原因与当时的 SQL）。"""
    from . import progress

    data = progress.load()
    out = []
    for q in questions:
        d = data.get(q["id"]) or {}
        ms = d.get("mistakes") or []
        if not ms or d.get("solved"):
            continue
        last = ms[-1]
        out.append({
            "id": q["id"], "title": q["title"], "stage": q["stage"],
            "tags": q.get("tags", []),
            "fails": len(ms), "attempts": d.get("attempts", 0),
            "last_at": last.get("at"), "last_message": (last.get("message") or "")[:200],
            "last_sql": (last.get("sql") or "")[:600],
        })
    out.sort(key=lambda x: (-x["fails"], x["stage"], x["id"]))
    return out
