# -*- coding: utf-8 -*-
"""按页面内容校验候选校招官网：抓 title + 检查公司名/招聘关键词，排除泛解析假阳性。"""
import subprocess, re, concurrent.futures as cf, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# (公司, 关键词列表, [候选URL])
T = [
    ("奥克斯",   ["奥克斯", "AUX"], ["https://www.auxgroup.com/", "https://aux.zhiye.com/campus", "https://hr.auxgroup.com/"]),
    ("春风动力", ["春风动力", "CFMOTO"], ["https://hr.cfmoto.com/", "https://www.cfmoto.com/"]),
    ("远景能源", ["远景", "Envision"], ["https://www.envision-group.com/", "https://careers.envision-group.com/"]),
    ("巨人网络", ["巨人网络", "巨人"], ["https://www.ga-me.com/", "https://hr.ga-me.com/"]),
    ("金风科技", ["金风", "Goldwind"], ["https://careers.goldwind.com/", "https://www.goldwind.com/"]),
    ("海信",     ["海信", "Hisense"], ["https://jobs.hisense.com/", "https://www.hisense.com/", "https://hr.hisense.com/"]),
    ("灵犀互娱", ["灵犀", "网易"], ["https://campus.163.com/", "https://hr.163.com/", "https://lingxi.163.com/"]),
    ("九号公司", ["九号", "Ninebot", "Segway"], ["https://www.ninebot.com/", "https://careers.ninebot.com/", "https://hr.ninebot.com/"]),
    ("叠纸游戏", ["叠纸", "恋与", "闪耀暖暖"], ["https://www.papegames.com/", "https://careers.papegames.com/"]),
    ("三一集团", ["三一", "SANY"], ["https://www.sany.com.cn/", "https://hr.sany.com.cn/", "https://sany.zhiye.com/campus"]),
    ("传音控股", ["传音", "Transsion", "TECNO"], ["https://www.transsion.com/", "https://careers.transsion.com/", "https://transsion.zhiye.com/campus"]),
    ("紫光展锐", ["紫光展锐", "展锐", "UNISOC", "SPRD"], ["https://www.unisoc.com/", "https://careers.unisoc.com/"]),
    ("阳光电源", ["阳光电源", "Sungrow"], ["https://jobs.sungrowpower.com/", "https://www.sungrowpower.com/", "https://careers.sungrowpower.com/"]),
    ("货拉拉",   ["货拉拉", "Lalamove", "Huolala"], ["https://hr.huolala.cn/", "https://www.huolala.cn/", "https://job.huolala.cn/campus"]),
    ("深蓝互动", ["深蓝互动", "深蓝"], ["https://www.darkblue.game/", "https://darkblue.zhiye.com/campus"]),
    ("途虎养车", ["途虎", "Tuhu"], ["https://hr.tuhu.cn/", "https://www.tuhu.cn/", "https://zhaopin.tuhu.cn/"]),
]

def fetch(u):
    try:
        r = subprocess.run(["curl", "-sS", "-L", "--max-time", "18", "-A", UA, u],
                           capture_output=True, timeout=25)
        raw = r.stdout
        for enc in ("utf-8", "gb18030"):
            try:
                html = raw.decode(enc, errors="strict")
                break
            except Exception:
                html = raw.decode(enc, errors="ignore")
        code = str(r.returncode)
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:90] if m else "(无title)"
        hits = [k for k in KW if k.lower() in html.lower()]
        return (u, code, title, hits, len(html))
    except Exception as e:
        return (u, "ERR", type(e).__name__, [], 0)

for name, KW, urls in T:
    print("\n=== %s ===" % name)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for u, code, title, hits, ln in ex.map(fetch, urls):
            flag = "✅命中" if hits else "  ---"
            print("  %s %-46s 标题: %-34s 命中: %s 大小:%d" % (flag, u, title[:34], ",".join(hits) or "无", ln))
    sys.stdout.flush()
