# -*- coding: utf-8 -*-
"""批量把已确认失效的校招链接替换为核实过的新入口（逐条打印，可核对）。"""
import io, sys

P = "build_workbench.py"
# 旧URL -> (新URL, 说明)
REPL = {
    "https://campus.auxgroup.com/":        ("https://www.auxgroup.com/", "奥克斯官网"),
    "https://campus.cfmoto.com/":          ("https://www.cfmoto.com/", "春风动力官网"),
    "https://campus.envision-group.com/":  ("https://envision-career.com", "远景校招官网"),
    "https://campus.ga-me.com/":           ("https://hr.ztgame.com/campus/join/recruit/", "巨人网络校招"),
    "https://campus.goldwind.com/":        ("https://www.goldwind.com/", "金风科技官网"),
    "https://campus.hisense.com/":         ("https://jobs.hisense.com/", "海信招聘官网"),
    "https://campus.lingxi.163.com/":      ("https://campus.163.com/", "网易(灵犀)校招"),
    "https://campus.ninebot.com/":         ("https://www.ninebot.com/", "九号公司官网"),
    "https://campus.papegames.com/":       ("https://www.papegames.com/", "叠纸游戏官网"),
    "https://campus.sany.com.cn/":         ("https://sany.zhiye.com/campus", "三一校招门户"),
    "https://campus.transsion.com/":       ("https://transsion.zhiye.com/campus", "传音校招门户"),
    "https://campus.unisoc.com/recruit":   ("https://www.unisoc.com/", "紫光展锐官网"),
    "https://careers.sungrowpower.com/campus": ("https://jobs.sungrowpower.com/", "阳光电源招聘"),
    "https://job.huolala.cn/campus":       ("https://join.huolala.cn/", "货拉拉招聘门户"),
    "https://www.darkblue.game/":          ("https://www.bluepoch.com/", "深蓝互动官网"),
    "https://zhaopin.tuhu.cn/":            ("https://www.tuhu.cn/", "途虎养车官网"),
}

src = io.open(P, encoding="utf-8").read()
total = 0
for old, (new, desc) in REPL.items():
    n = src.count(old)
    if n == 0:
        print("!! 未找到（可能已改或写法不同）: %s" % old)
        continue
    # 打印将被修改的行
    for line in src.split("\n"):
        if old in line:
            print("  改前: %s" % line.strip()[:100])
    src = src.replace(old, new)
    total += n
    print("  ✅ %-14s %s -> %s (替换 %d 处)" % (desc, old, new, n))

io.open(P, "w", encoding="utf-8").write(src)
print("\n共替换 %d 处" % total)

# 复核：还有多少已确认废弃域名残留
left = [d for d in REPL if d in src]
print("残留废弃域名:", left if left else "无 ✅")
