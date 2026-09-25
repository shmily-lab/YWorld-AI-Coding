# -*- coding: utf-8 -*-
"""数据库学习工作台 · 命令行入口。

    python run.py init                      重建沙箱数据库
    python run.py schema                    打印表结构
    python run.py list  [--stage N]         列出题目
    python run.py show  S1-Q01              查看题面（不显示答案）
    python run.py reveal S1-Q01             查看答案与讲解
    python run.py step  S1-Q01              逐条查看解题思路（不剧透答案）
    python run.py check S1-Q01 [-f a.sql] [-s "SELECT ..."]   提交判分
    python run.py exam  --stage 3 [-n 5]    闯关模式
    python run.py review [--do]             今日复习队列（--do 直接进入作答）
    python run.py wrong  [--do]             错题集（--do 重做未攻克的题）
    python run.py diagnose                  薄弱点诊断 + 重点训练建议
    python run.py note   S1-Q01             给题目写笔记（交互式）
    python run.py notes  [-o file.md]       导出全部笔记与标记
    python run.py reset --question S3-Q03   重做这一题（保留笔记）
    python run.py reset --stage 3           重置整个阶段
    python run.py reset --all               清空全部学习记录（自动备份）
    python run.py progress                  查看学习进度
    python run.py selftest                  题库自检
    python run.py web  [--port 8787]        启动浏览器练习环境
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import db, grader, progress, review  # noqa: E402
from engine.loader import all_questions, by_id, stages  # noqa: E402

DIFF_COLOR = {"easy": "\033[32m入门\033[0m", "medium": "\033[33m进阶\033[0m", "hard": "\033[31m挑战\033[0m"}


def _read_sql(args) -> str | None:
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            return f.read()
    if args.sql:
        return args.sql
    print("在下方输入你的 SQL，单起一行只写 ; 表示结束：")
    lines = []
    while True:
        try:
            line = input("sql> ")
        except EOFError:
            break
        if line.strip() == ";":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _input_sql(prompt: str = "sql> ") -> tuple[str, str]:
    """交互式读一段 SQL。返回 (sql, 控制指令)。"""
    print("（输入 SQL；仅输入 skip 跳过；quit 退出；think 看解题思路；ans 看答案）")
    lines = []
    while True:
        try:
            line = input(prompt)
        except EOFError:
            return "\n".join(lines).strip(), "quit"
        s = line.strip()
        if s in ("skip", "quit", "think", "ans") and not lines:
            return "", s
        if s == ";" and lines:
            break
        lines.append(line)
    return "\n".join(lines).strip(), ""


# --------------------------------------------------------------------------
def cmd_init(_a):
    import sandbox.seed  # noqa: E402
    sys.modules["sandbox.seed"].build()


def cmd_schema(_a):
    con = db.connect(db.TEMPLATE_DB)
    info = db.schema_info(con)
    for t, meta in info.items():
        cols = ", ".join(
            f"{c['name']} {c['type']}"
            + (" PK" if c["pk"] else "")
            + (" NOT NULL" if c["notnull"] else "")
            + (f" DEFAULT {c['default']}" if c["default"] is not None else "")
            for c in meta["columns"])
        print(f"{t}  ({meta['rows']} 行)\n    {cols}")
    con.close()


def cmd_list(a):
    qs = all_questions()
    if a.stage:
        qs = [q for q in qs if q["stage"] == a.stage]
    cur_stage = None
    done = progress.load()
    for q in qs:
        if q["stage"] != cur_stage:
            cur_stage = q["stage"]
            print(f"\n=== 阶段 {cur_stage}：{stages()[cur_stage]} ===")
        d = done.get(q["id"]) or {}
        flag = "✅" if d.get("passed") else ("❌" if d.get("mistakes") else "  ")
        mark = {"star": "⭐", "flag": "❗", "done": "✓"}.get(d.get("mark", ""), " ")
        kind = " [融合题]" if q.get("kind") == "review" else ""
        print(f"{flag}{mark} {q['id']}  {q['title']}{kind}  "
              f"[{DIFF_COLOR[q['difficulty']]} / {q['points']}分]")
    print(f"\n共 {len(qs)} 题")


def cmd_show(a):
    q = by_id(a.qid)
    if not q:
        return print(f"未找到题目 {a.qid}")
    print(f"\n【{q['id']}】{q['title']}  阶段{q['stage']} | {q['difficulty']} | {q['points']}分")
    print("知识点：" + "、".join(q.get("tags") or ["—"]) + "\n")
    print(q["prompt"].strip())
    if q.get("hint"):
        print(f"\n💡 提示：{q['hint'].strip()}")


def cmd_step(a):
    """逐条展示解题思路，按回车继续。"""
    q = by_id(a.qid)
    if not q:
        return print(f"未找到题目 {a.qid}")
    steps = q.get("approach") or []
    if not steps:
        return print("本题暂无解题思路，可先卡一卡再看 `reveal`。")
    print(f"\n【{q['id']}】解题思路（共 {len(steps)} 步，每步只给方向，不给答案）\n")
    for i, s in enumerate(steps, 1):
        try:
            input(f"▶ 第 {i} 步（回车展开）...")
        except EOFError:
            pass
        print(f"   {i}. {s}\n")
    print("全部思路已给出。还没有头绪就 `python run.py reveal %s` 看参考实现。" % q["id"])


def cmd_reveal(a):
    q = by_id(a.qid)
    if not q:
        return print(f"未找到题目 {a.qid}")
    ans = q["verify"].get("answer") or q["verify"].get("check")
    print(f"\n--- 参考实现 ---\n{ans}")
    if q.get("teach"):
        print(f"\n--- 讲解 ---\n{q['teach'].strip()}")


def cmd_check(a):
    from engine.grader import grade
    q = by_id(a.qid)
    if not q:
        return print(f"未找到题目 {a.qid}")
    sql = _read_sql(a)
    if not sql or not sql.strip():
        return print("没有输入 SQL")
    r = grade(q, sql)
    print("\n" + ("=" * 60))
    print(("✅ 通过" if r["ok"] else "❌ 未通过") + f"  [{q['id']}] {q['title']}")
    print("=" * 60)
    print(r["message"])
    if r.get("rows"):
        print("\n实际结果：")
        print(" | ".join(r.get("columns") or []))
        for row in r["rows"][:20]:
            print(" | ".join("NULL" if v is None else str(v) for v in row))
        if r.get("truncated"):
            print("... (结果过多已截断)")
    if not r["ok"] and r.get("expected_rows"):
        print("\n期望结果（前 10 行）：")
        print(" | ".join(r.get("expected_columns") or []))
        for row in r["expected_rows"][:10]:
            print(" | ".join("NULL" if v is None else str(v) for v in row))
    progress.record(q["id"], r["ok"], sql, r["message"])
    ent = progress.load()[q["id"]]
    print(f"\n本题尝试 {ent['attempts']} 次，通过状态：{'是' if ent['passed'] else '否'}"
          f"｜下次复习：{ent.get('next_review') or '—'}")


def _interactive(qs: list[dict], title: str):
    """通用的交互式作答循环，供 exam / review / wrong 复用。"""
    from engine.grader import grade
    if not qs:
        print("没有待做的题目。")
        return 0
    print(f"\n===== {title}：共 {len(qs)} 题 =====")
    score = 0
    for q in qs:
        cmd_show(type("A", (), {"qid": q["id"]})())
        while True:
            sql, ctrl = _input_sql()
            if ctrl == "quit":
                print(f"\n本轮得分 {score} 分")
                return score
            if ctrl == "skip":
                print("已跳过\n")
                break
            if ctrl == "think":
                cmd_step(type("A", (), {"qid": q["id"]})())
                continue
            if ctrl == "ans":
                cmd_reveal(type("A", (), {"qid": q["id"]})())
                continue
            if not sql:
                continue
            r = grade(q, sql)
            print(("✅ 通过\n" if r["ok"] else f"❌ 未通过：{r['message']}\n"))
            progress.record(q["id"], r["ok"], sql, r["message"])
            if r["ok"]:
                score += q.get("points", 0)
            else:
                d = progress.load()[q["id"]]
                print(f"（已记入错题本，累计错 {len(d.get('mistakes') or [])} 次；"
                      f"输入 think 看思路，ans 看答案）")
            break
    print(f"\n本轮得分 {score} 分")
    return score


def cmd_exam(a):
    qs = all_questions()
    if a.stage:
        qs = [q for q in qs if q["stage"] == a.stage]
    done = progress.load()
    qs = [q for q in qs if not (done.get(q["id"]) or {}).get("passed")]
    if a.n:
        qs = qs[: a.n]
    _interactive(qs, f"闯关 · 阶段{a.stage or '全部'}")


def cmd_review(a):
    qs = all_questions()
    due = review.due_today(qs)
    if not due:
        print("\n今天没有到期的复习任务 🎉")
        print("  新做的题会在 1 天后进入复习队列，答对则间隔逐级拉长（1/2/4/7/15/30/60 天）。")
        return
    print(f"\n===== 今日复习队列：{len(due)} 题 =====")
    for i, d in enumerate(due, 1):
        extra = ""
        if d["requires"]:
            extra = f"（综合阶段 { '/'.join(map(str, d['requires'])) }）"
        print(f"{i:>2}. [{d['reason']}] {d['id']} {d['title']}{extra}")
        if d["tags"]:
            print(f"     知识点：{'、'.join(d['tags'])}")
    if a.do:
        ids = [d["id"] for d in due]
        _interactive([q for q in qs if q["id"] in ids], "今日复习")


def cmd_wrong(a):
    qs = all_questions()
    ws = review.wrong_set(qs)
    if not ws:
        print("\n错题本是空的 ✅ 要么全对，要么还没开始做。")
        return
    print(f"\n===== 错题本：{len(ws)} 题（按错误次数排序）=====")
    for w in ws:
        print(f"\n❌ {w['id']} {w['title']}   错 {w['fails']} 次 / 共尝试 {w['attempts']} 次")
        print(f"   知识点：{'、'.join(w['tags']) or '—'}")
        print(f"   最近错误：{w['last_message']}")
        if w["last_sql"]:
            first = w["last_sql"].splitlines()[0][:70]
            print(f"   当时写的：{first} ...")
    if a.do:
        ids = [w["id"] for w in ws]
        _interactive([q for q in qs if q["id"] in ids], "错题重做")


def _pad(s: str, width: int = 14) -> str:
    """按显示宽度补齐空格（中文字符按两格算）。"""
    w = sum(2 if ord(c) > 0x2E80 else 1 for c in s)
    return " " * max(1, width - w)


def cmd_diagnose(_a):
    qs = all_questions()
    d = review.diagnose(qs)
    o = d["overall"]
    print("\n===== 学习诊断 =====")
    print(f"已练 {o['attempted']} 题，通过 {o['passed']} 题；"
          f"平均每题尝试 {o['avg_attempts']} 次；一次做对率 {o['first_try_rate']}%\n")

    if d["focus"]:
        print("⚠️  建议优先补这几块（按短板程度排序）：")
        for i, f in enumerate(d["focus"], 1):
            q = f["quality"]
            qs_txt = f"{int(q * 100)}%" if q is not None else "未练"
            print(f"\n  {i}. 【{f['tag']}】{f['level']}（掌握度 {qs_txt}）")
            print(f"     {f['reason']}")
            print(f"     重点练：{'、'.join(f['drill'])}")
    else:
        print("✅ 暂时没有明显短板，继续保持。")

    print("\n----- 各知识点掌握度 -----")
    for b in d["tags"]:
        if b["quality"] is None:
            bar = "·" * 10
            pct = "  —  "
        else:
            n = int(round(b["quality"] * 10))
            bar = "█" * n + "░" * (10 - n)
            pct = f"{int(b['quality'] * 100):>3}%"
        flag = {"薄弱": " ⚠️", "一般": " ·", "掌握": " ✓", "未练习": ""}.get(b["level"], "")
        # 中文字符占两个显示宽度，用等宽 padding 修一下
        print(f"  {b['tag']}{_pad(b['tag'])} {bar} {pct}  {b['level']}{flag}")
    print(f"\n提示：python run.py review --do  立即开始今日复习")


def cmd_reset(a):
    """重置学习记录（不是数据库）。用于「隔段时间重做一遍」。"""
    qs = all_questions()
    keep = "" if a.hard else "（保留笔记与标记）"
    if a.question:
        q = by_id(a.question)
        if not q:
            return print(f"未找到题目 {a.question}")
        progress.reset_question(q["id"], hard=a.hard)
        return print(f"✅ 已重置 {q['id']} {q['title']}{keep or '（含笔记）'}")
    if a.stage is not None:
        ids = [q["id"] for q in qs if q["stage"] == a.stage]
        n = progress.reset_many(ids, hard=a.hard)
        return print(f"✅ 已重置阶段 {a.stage} 的 {n} 题{keep or '（含笔记）'}")
    if a.all:
        b = progress.backup()
        n = progress.clear_all(hard=a.hard)
        print(f"✅ 已清空全部 {n} 题的学习记录{keep or '（含笔记）'}")
        return print(f"   备份在：{b}")
    print("重置哪一部分？")
    print("  单题    python run.py reset --question S3-Q03")
    print("  某阶段  python run.py reset --stage 3")
    print("  全部    python run.py reset --all")
    print("\n默认保留笔记、标记与划重点；加 --hard 一起清掉。")


def cmd_note(a):
    q = by_id(a.qid)
    if not q:
        return print(f"未找到题目 {a.qid}")
    cur = progress.get(q["id"])
    print(f"【{q['id']}】{q['title']}")
    if cur.get("note"):
        print(f"已有笔记：\n{cur['note']}\n")
    print("输入新笔记（覆盖旧的）；直接回车取消：")
    try:
        text = input("note> ")
    except EOFError:
        return
    if text.strip():
        progress.set_note(q["id"], text.strip())
        print("已保存笔记 ✅")
    print("标记：1=⭐收藏  2=❗易错（会进复习队列）  3=✓已掌握  0=清除")
    try:
        m = input("mark> ").strip()
    except EOFError:
        return
    progress.set_mark(q["id"], {"1": "star", "2": "flag", "3": "done", "0": ""}.get(m, ""))
    print("已保存标记 ✅")


def cmd_notes(a):
    text = progress.notes_markdown(all_questions())
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已导出笔记 → {a.out}")
    else:
        print(text)


def cmd_progress(_a):
    qs = all_questions()
    s = progress.summary(qs)
    t = s["total"]
    print(f"\n总进度：{t['passed']}/{t['total']} 题，{t['earned']}/{t['points']} 分"
          f"（累计提交 {t['attempts']} 次）")
    for st in sorted(s["stages"]):
        b = s["stages"][st]
        pct = int(b["passed"] / b["total"] * 100) if b["total"] else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        print(f"  阶段{st:<2} {stages()[st]:<12} {bar} {b['passed']}/{b['total']} 题 "
              f"({b['earned']}/{b['points']}分)")
    if s["wrong_cnt"]:
        print(f"\n❌ 错题本还有 {s['wrong_cnt']} 题未攻克：`python run.py wrong --do`")


def cmd_selftest(_a):
    rep = grader.selfcheck_report(all_questions())
    bad = [r for r in rep if not r[1]]
    for qid, ok, msg in rep:
        if not ok:
            print(f"❌ {qid}: {msg}")
    print(f"\n自检完成：{len(rep) - len(bad)}/{len(rep)} 题可用")
    return 0 if not bad else 1


def cmd_web(a):
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "server.py")
    sys.exit(subprocess.call([sys.executable, script, "--port", str(a.port)]))


def main():
    p = argparse.ArgumentParser(description="数据库学习工作台")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("schema").set_defaults(func=cmd_schema)

    c = sub.add_parser("list"); c.add_argument("--stage", type=int); c.set_defaults(func=cmd_list)
    c = sub.add_parser("show"); c.add_argument("qid"); c.set_defaults(func=cmd_show)
    c = sub.add_parser("step"); c.add_argument("qid"); c.set_defaults(func=cmd_step)
    c = sub.add_parser("reveal"); c.add_argument("qid"); c.set_defaults(func=cmd_reveal)
    c = sub.add_parser("check"); c.add_argument("qid")
    c.add_argument("-f", "--file"); c.add_argument("-s", "--sql")
    c.set_defaults(func=cmd_check)
    c = sub.add_parser("exam"); c.add_argument("--stage", type=int); c.add_argument("-n", type=int)
    c.set_defaults(func=cmd_exam)
    c = sub.add_parser("review"); c.add_argument("--do", action="store_true")
    c.set_defaults(func=cmd_review)
    c = sub.add_parser("wrong"); c.add_argument("--do", action="store_true")
    c.set_defaults(func=cmd_wrong)
    sub.add_parser("diagnose").set_defaults(func=cmd_diagnose)
    c = sub.add_parser("note"); c.add_argument("qid"); c.set_defaults(func=cmd_note)
    c = sub.add_parser("notes"); c.add_argument("-o", "--out"); c.set_defaults(func=cmd_notes)
    c = sub.add_parser("reset", help="重置学习记录：重做某题 / 某阶段 / 全部")
    c.add_argument("--question"); c.add_argument("--stage", type=int)
    c.add_argument("--all", action="store_true")
    c.add_argument("--hard", action="store_true", help="连笔记与标记一起清")
    c.set_defaults(func=cmd_reset)
    sub.add_parser("progress").set_defaults(func=cmd_progress)
    sub.add_parser("selftest").set_defaults(func=cmd_selftest)
    c = sub.add_parser("web"); c.add_argument("--port", type=int, default=8787)
    c.set_defaults(func=cmd_web)

    a = p.parse_args()
    if not a.cmd:
        return p.print_help()
    return a.func(a)


if __name__ == "__main__":
    main()
