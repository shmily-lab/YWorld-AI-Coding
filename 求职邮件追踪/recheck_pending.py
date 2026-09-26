# -*- coding: utf-8 -*-
"""用完整浏览器请求头复测"待确认"链接，区分真死链 vs 反爬/临时故障。"""
import subprocess, re, concurrent.futures as cf

H = [
    "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
    "-H", "Accept-Encoding: gzip, deflate",
    "-H", "Connection: keep-alive",
    "-H", "Upgrade-Insecure-Requests: 1",
]

T = [
    ("华为",       "https://career.huawei.com/cn/campus-recruitment.html", ["华为", "HUAWEI", "校园招聘"]),
    ("蔚来",       "https://campus.nio.com",                              ["蔚来", "NIO"]),
    ("小米",       "https://xiaomi.jobs.f.mioffice.cn/s/AvRsw8CHbRY",      ["小米", "Xiaomi"]),
    ("国家电网",    "https://zhaopin.sgcc.com.cn",                          ["国家电网", "SGCC", "招聘"]),
    ("长亭科技",    "https://campus2027.chaitin.cn/",                       ["长亭", "chaitin"]),
    ("天融信",     "https://www.topsec.com.cn/hr/campus.html",             ["天融信", "topsec"]),
    ("联想",       "https://campus.lenovo.com.cn/",                         ["联想", "Lenovo"]),
    ("三七互娱",    "https://campus.37.com/",                               ["三七", "37"]),
    ("华勤技术",    "https://campus.huaqin.com/",                           ["华勤", "huaqin"]),
    ("微软中国",    "https://careers.microsoft.com/",                       ["Microsoft", "微软"]),
    ("建设银行",    "http://job.ccb.com",                                   ["建设银行", "CCB"]),
    ("上汽集团",    "https://saic-recruit.saicmotor.com",                   ["上汽", "SAIC"]),
    ("问卷(mokahr)", "https://app.mokahr.com/su/vrhwod",                    ["mokahr"]),
]


def probe(t):
    name, url, kws = t
    try:
        r = subprocess.run(["curl", "-sS", "-L", "--compressed", "--max-time", "30",
                            "-w", "\n__C__%{http_code}__U__%{url_effective}"] + H + [url],
                           capture_output=True, timeout=40)
        txt = r.stdout.decode("utf-8", errors="ignore")
        m = re.search(r"__C__(\d{3})__U__(.*)", txt, re.S)
        code = m.group(1) if m else "000"
        final = (m.group(2).strip() if m else url)[:60]
        body = txt.split("__C__")[0]
        mt = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
        title = re.sub(r"\s+", " ", mt.group(1)).strip()[:40] if mt else "(无)"
        hits = [k for k in kws if k.lower() in body.lower()]
        return (name, url, code, title, hits, len(body), final)
    except subprocess.TimeoutExpired:
        return (name, url, "TIMEOUT", "-", [], 0, "-")
    except Exception as e:
        return (name, url, "EXC:" + type(e).__name__, "-", [], 0, "-")


with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for name, url, code, title, hits, ln, final in ex.map(probe, T):
        if code.startswith("2") and (hits or ln > 2000):
            verdict = "✅ 正常"
        elif code.startswith("2"):
            verdict = "⚠️ 200但内容空(疑似反爬/SPA)"
        elif code in ("403", "412", "429"):
            verdict = "⚠️ 反爬拦截(非死链)"
        elif code in ("000", "TIMEOUT") or code.startswith("EXC"):
            verdict = "❓ 连不上(需人工在浏览器试)"
        else:
            verdict = "❌ 异常 HTTP " + code
        print("%-12s %-56s %s\n              标题:%-28s 命中:%-14s 大小:%-7d 终址:%s" %
              (name, url, verdict, title[:28], ",".join(hits) or "无", ln, final))
