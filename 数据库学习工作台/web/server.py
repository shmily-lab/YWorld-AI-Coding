# -*- coding: utf-8 -*-
"""本地 SQL 练习工作台（零第三方依赖）

启动：
    python web/server.py --port 8787
然后浏览器打开 http://127.0.0.1:8787

设计要点：
1. 只用标准库：http.server + sqlite3，不需要 pip install 任何东西。
2. 会话隔离：每个浏览器会话拥有一份 learn.db 的独立副本 sxx.db，
   随便改随便删，不影响题库基准、也不影响其他会话。
3. 判分隔离：提交判分时再拿一份全新副本执行，因此重复提交同一条 SQL 结果完全一致，
   不会出现「第二次提交因为数据已经被改掉而判错」。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import db, progress, review  # noqa: E402
from engine.grader import grade  # noqa: E402
from engine.loader import STAGE_NAMES, all_questions, by_id, public_view  # noqa: E402

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

MAX_BODY = 512 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "DBWorkbench/1.0"

    # ------------------------------------------------------------ 工具
    def log_message(self, fmt, *args):  # 只在/, /api 报错时打印，减少噪音
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _html(self, path: str):
        with open(path, "rb") as f:
            self._send(200, f.read(), "text/html; charset=utf-8")

    def _body_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            return {}
        raw = self.rfile.read(n) if n else b"{}"
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    # ------------------------------------------------------------ 路由
    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        p, qs = u.path, parse_qs(u.query)

        if p in ("/", "/index.html"):
            return self._html(os.path.join(STATIC_DIR, "index.html"))

        if p == "/api/stages":
            return self._json({"stages": [{"id": k, "name": v} for k, v in sorted(STAGE_NAMES.items())]})

        if p == "/api/questions":
            qs_all = all_questions()
            data = progress.load()
            items = [public_view(q) for q in qs_all]
            for it in items:
                d = data.get(it["id"]) or {}
                it["passed"] = bool(d.get("passed"))
                it["attempts"] = int(d.get("attempts") or 0)
                it["mark"] = d.get("mark", "")
                it["note"] = d.get("note", "")
                it["highlights"] = d.get("highlights") or []
                it["next_review"] = d.get("next_review")
                it["fails"] = len(d.get("mistakes") or [])
                it["solved"] = bool(d.get("solved"))
                it["unlocked"] = (review.review_unlocked(it, qs_all, data)
                                  if it.get("kind") == "review" else True)
            return self._json({"questions": items,
                               "stages": STAGE_NAMES,
                               "total": len(items)})

        if p == "/api/due":
            return self._json({"due": review.due_today(all_questions())})

        if p == "/api/mistakes":
            return self._json({"mistakes": review.wrong_set(all_questions())})

        if p == "/api/diagnose":
            return self._json(review.diagnose(all_questions()))

        if p == "/api/approach":
            q = by_id((qs.get("qid") or [""])[0])
            if not q:
                return self._json({"error": "题目不存在"}, 404)
            return self._json({"id": q["id"], "approach": q.get("approach", [])})

        if p == "/api/notes":
            return self._json({"markdown": progress.notes_markdown(all_questions())})

        if p == "/api/schema":
            con = db.connect(db.session_db((qs.get("session") or ["web"])[0]))
            try:
                return self._json({"schema": db.schema_info(con)})
            finally:
                con.close()

        if p == "/api/answer":
            q = by_id((qs.get("qid") or [""])[0])
            if not q:
                return self._json({"error": "题目不存在"}, 404)
            return self._json({"id": q["id"],
                               "answer": q["verify"].get("answer", ""),
                               "teach": q.get("teach", "")})

        if p == "/api/progress":
            return self._json(progress.summary(all_questions()))

        self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):  # noqa: N802
        p = urlparse(self.path).path
        body = self._body_json()

        if p == "/api/query":
            sess = body.get("session") or "web"
            sql = body.get("sql") or ""
            con = db.connect(db.session_db(sess))
            try:
                t0 = time.perf_counter()
                res = db.execute(con, sql, max_rows=1000)
                res["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
                res["rows"] = db.rows_to_lists(res["rows"])
                return self._json(res)
            finally:
                con.close()

        if p == "/api/check":
            q = by_id(body.get("qid") or "")
            if not q:
                return self._json({"error": "题目不存在"}, 404)
            sql = body.get("sql") or ""
            try:
                r = grade(q, sql)
            except FileNotFoundError as e:
                return self._json({"error": str(e)}, 500)
            rec = progress.record(q["id"], bool(r["ok"]), sql, r.get("message", ""))
            r["recorded"] = True
            r["review"] = {"attempts": rec.get("attempts"),
                           "next_review": rec.get("next_review"),
                           "solved": bool(rec.get("solved"))}
            return self._json(r)

        if p == "/api/reset":
            sess = body.get("session") or "web"
            db.reset_session(sess)
            return self._json({"ok": True, "session": sess})

        if p == "/api/mark":
            qid = body.get("qid") or ""
            return self._json({"mark": progress.set_mark(qid, body.get("mark", "")).get("mark", "")})

        if p == "/api/note":
            qid = body.get("qid") or ""
            return self._json({"note": progress.set_note(qid, body.get("text", "")).get("note", "")})

        if p == "/api/highlight":
            qid = body.get("qid") or ""
            ent = progress.add_highlight(qid, body.get("text", ""), body.get("note", ""))
            return self._json({"highlights": ent.get("highlights", [])})

        if p == "/api/unhighlight":
            qid = body.get("qid") or ""
            return self._json({"highlights": progress.clear_highlights(qid).get("highlights", [])})

        if p == "/api/reset-progress":
            """重置学习记录。scope: question / stage / all；hard 连笔记一起清。"""
            scope = body.get("scope", "question")
            hard = bool(body.get("hard"))
            qs = all_questions()
            if scope == "question":
                qid = body.get("qid") or ""
                if not by_id(qid):
                    return self._json({"error": "题目不存在"}, 404)
                progress.reset_question(qid, hard=hard)
                return self._json({"ok": True, "reset": 1})
            if scope == "stage":
                st = int(body.get("stage") or 0)
                ids = [q["id"] for q in qs if q["stage"] == st]
                return self._json({"ok": True, "reset": progress.reset_many(ids, hard=hard)})
            if scope == "all":
                bk = progress.backup()
                return self._json({"ok": True, "reset": progress.clear_all(hard=hard),
                                   "backup": bk})
            return self._json({"error": f"未知 scope：{scope}"}, 400)

        self._send(404, b"not found", "text/plain; charset=utf-8")


def main():
    ap = argparse.ArgumentParser(description="数据库学习工作台 Web 界面")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(db.TEMPLATE_DB):
        print("模板库不存在，请先执行： python run.py init")
        sys.exit(1)

    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    url = f"http://{a.host}:{a.port}"
    print(f"工作台已启动：{url}")
    print("停止服务：Ctrl+C")
    if not a.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        srv.server_close()


if __name__ == "__main__":
    main()
