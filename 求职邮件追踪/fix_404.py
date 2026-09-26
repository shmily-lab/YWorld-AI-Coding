# -*- coding: utf-8 -*-
"""修正 HTTP 404（路径写错）的链接。"""
import io

P = "build_workbench.py"
REPL = {
    "https://www.wps.cn/hr/":                        ("https://www.wps.cn/", "金山办公WPS"),
    "https://www.keyence.com.cn/recruit/":           ("https://www.keyence.com.cn/careers", "基恩士"),
    "https://www.hypergryph.com/campus":             ("https://www.hypergryph.com/", "鹰角网络"),
    "https://www.smics.com/campus":                  ("https://www.smics.com/", "中芯国际"),
    "https://www.sunwoda.com/campus":                ("https://www.sunwoda.com/", "欣旺达"),
    "https://www.himile.com/campus":                 ("https://www.himile.com/", "豪迈集团"),
    "https://www.dbappsecurity.com.cn/careers":      ("https://www.dbappsecurity.com.cn/", "安恒信息"),
    "http://hillstonenet.m.zhiye.com":               ("https://hillstonenet.zhiye.com/campus", "山石网科"),
    "https://cgn.hotjob.cn":                         ("https://www.cgnpc.com.cn/", "中广核"),
}

src = io.open(P, encoding="utf-8").read()
total = 0
for old, (new, desc) in REPL.items():
    n = src.count(old)
    if n == 0:
        print("!! 未找到: %s (%s)" % (old, desc))
        continue
    for line in src.split("\n"):
        if old in line:
            print("  改前: %s" % line.strip()[:95])
    src = src.replace(old, new)
    total += n
    print("  ✅ %-12s -> %s (%d 处)" % (desc, new, n))

io.open(P, "w", encoding="utf-8").write(src)
print("\n共替换 %d 处" % total)
