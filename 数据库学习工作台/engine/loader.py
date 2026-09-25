# -*- coding: utf-8 -*-
"""扫描 questions/ 目录下所有 stage*.py，聚合成题库，并合并 meta.py 里的标签与思路。"""
from __future__ import annotations

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_DIR = os.path.join(ROOT, "questions")

STAGE_NAMES = {
    1: "查询基础",
    2: "聚合与分组",
    3: "多表连接",
    4: "子查询与 CTE",
    5: "窗口函数",
    6: "数据变更与事务",
    7: "建模与约束",
    8: "索引与执行计划",
    9: "调优实战",
    10: "综合融合作战",
}

_cache: list[dict] | None = None


def stages() -> dict:
    return STAGE_NAMES


def _import(name: str):
    path = os.path.join(QUESTIONS_DIR, f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"q_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def all_questions(refresh: bool = False) -> list[dict]:
    global _cache
    if _cache is not None and not refresh:
        return _cache

    meta = _import("meta")
    tags, approach = meta.TAGS, meta.APPROACH

    qs: list[dict] = []
    for fn in sorted(os.listdir(QUESTIONS_DIR)):
        if not (fn.startswith("stage") and fn.endswith(".py")):
            continue
        mod = _import(fn[:-3])
        for q in mod.QUESTIONS:
            # 标签与解题思路单独维护，避免改题面时误伤分类
            q["tags"] = tags.get(q["id"], [])
            q["approach"] = approach.get(q["id"], [])
            q.setdefault("kind", "normal")
            qs.append(q)
    qs.sort(key=lambda q: (q["stage"], q["id"]))
    _cache = qs
    return qs


def tag_stage() -> dict:
    """标签 → 所属阶段映射（来自 questions/meta.py）。"""
    return _import("meta").TAG_STAGE


def by_id(qid: str) -> dict | None:
    for q in all_questions():
        if q["id"] == qid:
            return q
    return None


def public_view(q: dict) -> dict:
    """脱敏视图：不含参考答案，供前端展示。"""
    return {
        "id": q["id"], "stage": q["stage"], "title": q["title"],
        "difficulty": q["difficulty"], "points": q["points"],
        "kind": q.get("kind", "normal"), "requires": q.get("requires", []),
        "covers": q.get("covers", []),
        "prompt": q["prompt"], "hint": q.get("hint", ""),
        "approach": q.get("approach", []), "tags": q.get("tags", []),
        "mode": q["verify"].get("mode", "exact"),
    }
