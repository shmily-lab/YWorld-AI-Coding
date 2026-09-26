# -*- coding: utf-8 -*-
"""候选校招官网批量探测：对失效链接的公司，按常见规律生成候选 URL 并实测 HTTP 状态。"""
import subprocess, concurrent.futures as cf, sys

# (公司名, 主域名, [拼音/英文品牌候选])
TARGETS = [
    ("奥克斯",   "auxgroup.com",     ["aux", "auxgroup"]),
    ("春风动力", "cfmoto.com",       ["cfmoto"]),
    ("远景能源", "envision-group.com", ["envision", "envisiongroup"]),
    ("巨人网络", "ga-me.com",        ["game", "gamе", "giant"]),
    ("金风科技", "goldwind.com",     ["goldwind"]),
    ("海信",     "hisense.com",      ["hisense"]),
    ("灵犀互娱", "163.com",          ["lingxi"]),
    ("九号公司", "ninebot.com",      ["ninebot"]),
    ("叠纸游戏", "papegames.com",    ["papegames", "niepaper"]),
    ("三一集团", "sany.com.cn",      ["sany"]),
    ("传音控股", "transsion.com",    ["transsion"]),
    ("紫光展锐", "unisoc.com",       ["unisoc", "sprd"]),
    ("阳光电源", "sungrowpower.com", ["sungrow", "sungrowpower"]),
    ("货拉拉",   "huolala.cn",       ["huolala", "lalamove"]),
    ("深蓝互动", "darkblue.game",    ["darkblue"]),
    ("途虎养车", "tuhu.cn",          ["tuhu"]),
]

def cands(base, brands):
    out = []
    for b in ["https://" + base, "http://" + base]:
        out.append(b)
    for p in ["/campus", "/careers", "/jobs", "/job", "/recruit", "/campus2027"]:
        out.append("https://" + base + p)
    for sub in ["campus", "careers", "job", "jobs", "hr", "zhaopin"]:
        out.append("https://%s.%s" % (sub, base))
    for br in brands:
        out.append("https://%s.zhiye.com" % br)
        out.append("https://%s.zhiye.com/campus" % br)
    seen, uniq = set(), []
    for u in out:
        if u not in seen:
            seen.add(u); uniq.append(u)
    return uniq

def probe(u):
    try:
        r = subprocess.run(
            ["curl", "-sS", "-o", "NUL", "-w", "%{http_code}", "-L",
             "--max-time", "14", "-A",
             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36", u],
            capture_output=True, text=True, timeout=20)
        code = (r.stdout or "").strip()[-3:]
        return (u, code if code.isdigit() else "ERR")
    except Exception:
        return (u, "TIMEOUT")

for name, base, brands in TARGETS:
    urls = cands(base, brands)
    print("\n=== %s (主域名 %s) ===" % (name, base))
    good = []
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for u, code in ex.map(probe, urls):
            if code.startswith("2"):
                good.append((u, code))
    if good:
        for u, c in good:
            print("  [OK %s] %s" % (c, u))
    else:
        print("  (候选全灭，需人工联网查)")
    sys.stdout.flush()
