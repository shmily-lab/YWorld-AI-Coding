# -*- coding: utf-8 -*-
"""给 HTTP 404 的链接自动探测正确路径（按常见规律 + 内容校验）。"""
import subprocess, re, concurrent.futures as cf

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

T = [
    ("金山办公WPS", ["WPS", "金山办公"], "wps.cn",
     ["https://www.wps.cn/", "https://www.wps.cn/careers", "https://hr.wps.cn/", "https://careers.wps.cn/"]),
    ("基恩士", ["基恩士", "KEYENCE"], "keyence.com.cn",
     ["https://www.keyence.com.cn/", "https://www.keyence.com.cn/careers", "https://www.keyence.com.cn/recruit"]),
    ("鹰角网络", ["鹰角", "HYPERGRYPH", "明日方舟"], "hypergryph.com",
     ["https://www.hypergryph.com/", "https://www.hypergryph.com/careers", "https://careers.hypergryph.com/"]),
    ("中芯国际", ["中芯国际", "SMIC"], "smics.com",
     ["https://www.smics.com/", "https://www.smics.com/careers", "https://careers.smics.com/"]),
    ("欣旺达", ["欣旺达", "SUNWODA"], "sunwoda.com",
     ["https://www.sunwoda.com/", "https://www.sunwoda.com/careers", "https://hr.sunwoda.com/"]),
    ("豪迈集团", ["豪迈", "HIMILE"], "himile.com",
     ["https://www.himile.com/", "https://www.himile.com/careers", "https://hr.himile.com/"]),
    ("安恒信息", ["安恒", "DBAPPSecurity"], "dbappsecurity.com.cn",
     ["https://www.dbappsecurity.com.cn/", "https://www.dbappsecurity.com.cn/hr",
      "https://www.dbappsecurity.com.cn/campus", "https://careers.dbappsecurity.com.cn/"]),
    ("山石网科", ["山石网科", "Hillstone"], "hillstonenet.com",
     ["https://www.hillstonenet.com/", "https://www.hillstonenet.com/careers",
      "https://hillstonenet.zhiye.com/campus"]),
    ("中广核", ["中广核", "CGN"], "cgnpc.com.cn",
     ["https://www.cgnpc.com.cn/", "https://cgnpc.hotjob.cn/", "https://cgn.zhiye.com/campus"]),
]


def fetch(t):
    name, kws, dom, urls = t
    out = []
    for u in urls:
        try:
            r = subprocess.run(["curl", "-sS", "-L", "--max-time", "16", "-A", UA, u],
                               capture_output=True, timeout=22)
            h = r.stdout.decode("utf-8", errors="ignore")
            if not h.strip():
                h = r.stdout.decode("gb18030", errors="ignore")
            m = re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I)
            title = re.sub(r"\s+", " ", m.group(1)).strip()[:45] if m else "(无)"
            hits = [k for k in kws if k.lower() in h.lower()]
            out.append((u, title, hits, len(h)))
        except Exception as e:
            out.append((u, "EXC:" + type(e).__name__, [], 0))
    return (name, out)


with cf.ThreadPoolExecutor(max_workers=9) as ex:
    for name, rows in ex.map(fetch, T):
        print("\n=== %s ===" % name)
        for u, title, hits, ln in rows:
            ok = "✅" if (hits and ln > 500) else "  "
            print("  %s %-52s 标题:%-26s 命中:%-16s 大小:%d" %
                  (ok, u, title[:26], ",".join(hits) or "无", ln))
