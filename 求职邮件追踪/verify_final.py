# -*- coding: utf-8 -*-
"""最终选定链接的内容校验：确认页面真的是该公司的招聘/校招页。"""
import subprocess, re, concurrent.futures as cf

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
# (公司, 最终URL, 关键词)
FINAL = [
    ("奥克斯",   "https://www.auxgroup.com/",              ["奥克斯", "AUX"]),
    ("春风动力", "https://www.cfmoto.com/",                ["春风动力", "CFMOTO"]),
    ("远景能源", "https://envision-career.com",            ["远景", "Envision", "campus"]),
    ("巨人网络", "https://hr.ztgame.com/campus/join/recruit/", ["巨人", "ztgame", "征途"]),
    ("金风科技", "https://www.goldwind.com/",              ["金风", "Goldwind"]),
    ("海信",     "https://jobs.hisense.com/",              ["海信", "招聘"]),
    ("灵犀互娱", "https://campus.163.com/",                ["网易", "校园招聘"]),
    ("九号公司", "https://www.ninebot.com/",               ["九号", "Ninebot"]),
    ("叠纸游戏", "https://www.papegames.com/",             ["叠纸", "Papergames"]),
    ("三一集团", "https://sany.zhiye.com/campus",          ["三一", "SANY"]),
    ("传音控股", "https://transsion.zhiye.com/campus",     ["传音", "Transsion"]),
    ("紫光展锐", "https://www.unisoc.com/",                ["紫光展锐", "UNISOC"]),
    ("阳光电源", "https://jobs.sungrowpower.com/",         ["阳光电源", "招聘"]),
    ("货拉拉",   "https://join.huolala.cn/",               ["货拉拉", "校园招聘", "CAMPUS"]),
    ("深蓝互动", "https://campus.bluepoch.com",            ["深蓝", "bluepoch", "BLUEPOCH"]),
    ("途虎养车", "https://www.tuhu.cn/",                   ["途虎"]),
]

def fetch(item):
    name, u, kws = item
    try:
        r = subprocess.run(["curl", "-sS", "-L", "--max-time", "18", "-A", UA, u],
                           capture_output=True, timeout=25)
        html = r.stdout.decode("utf-8", errors="ignore")
        if not html.strip():
            html = r.stdout.decode("gb18030", errors="ignore")
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:70] if m else "(无)"
        hits = [k for k in kws if k.lower() in html.lower()]
        return (name, u, r.returncode, title, hits, len(html))
    except Exception as e:
        return (name, u, "EXC", type(e).__name__, [], 0)

with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for name, u, rc, title, hits, ln in ex.map(fetch, FINAL):
        ok = "OK " if hits and ln > 500 else "!! "
        print("%s%-8s %-52s 标题:%-30s 命中:%-22s 大小:%d" %
              (ok, name, u, title[:30], ",".join(hits) or "无", ln))
