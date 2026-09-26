# -*- coding: utf-8 -*-
"""
校招官网链接体检（DNS + HTTP 双重探测）

用法：
    python check_links.py

输出：
    - 控制台摘要
    - 同目录「链接体检报告.md」

判定分级：
    OK          HTTP 2xx/3xx 且页面有实质内容
    DNS失败      域名解析不了（域名已废弃/子域名猜错）→ 必改
    连接失败      能解析但连不上（站点挂了 / 旧域名被弃用）→ 必改
    HTTP错误     4xx/5xx → 需核实
    空内容       返回 200 但内容为空，多为反爬需真实浏览器 → 人工确认
"""
import re, io, os, socket, subprocess, concurrent.futures as cf, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "build_workbench.py")
REPORT = os.path.join(HERE, "链接体检报告.md")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# 已知"命令行访问会被拦/需真实浏览器"的域名，不算死链，仅提示
KNOWN_BROWSER_ONLY = ["mokahr.com", "zhiye.com", "envision-career.com"]


def extract():
    """从 build_workbench.py 抽出 (公司名, URL)。"""
    out = []
    for line in io.open(SRC, encoding="utf-8").read().split("\n"):
        if "http" not in line:
            continue
        urls = re.findall(r'https?://[^\s"\'),]+', line)
        if not urls:
            continue
        m = re.search(r'\("([^"]+)"', line)
        name = m.group(1) if m else "(未知)"
        for u in urls:
            out.append((name, u.rstrip('",)')))
    return out


def check(item):
    name, url = item
    host = re.match(r"https?://([^/:?#]+)", url)
    host = host.group(1) if host else ""
    # 1) DNS
    try:
        socket.setdefaulttimeout(6)
        socket.gethostbyname(host)
    except Exception:
        return (name, url, "DNS失败", "域名解析不了")
    # 2) HTTP
    try:
        r = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "18", "-A", UA,
             "-w", "\n__CODE__%{http_code}", url],
            capture_output=True, timeout=25)
        raw = r.stdout
        txt = raw.decode("utf-8", errors="ignore")
        m = re.search(r"__CODE__(\d{3})", txt)
        code = m.group(1) if m else "000"
        body = txt.split("__CODE__")[0]
        size = len(body)
        if code.startswith("2"):
            if size < 500:
                if any(k in host for k in KNOWN_BROWSER_ONLY):
                    return (name, url, "空内容", "疑似反爬，需真实浏览器确认")
                return (name, url, "空内容", "200 但内容为空，需人工确认")
            return (name, url, "OK", "HTTP %s，%d 字节" % (code, size))
        if code.startswith("3"):
            return (name, url, "OK", "HTTP %s 跳转" % code)
        return (name, url, "HTTP错误", "HTTP %s" % code)
    except subprocess.TimeoutExpired:
        return (name, url, "连接失败", "超时")
    except Exception:
        return (name, url, "连接失败", "连不上")


def main():
    items = extract()
    # 去重（同 URL 只测一次，但保留公司名）
    seen, uniq = {}, []
    for n, u in items:
        if u not in seen:
            seen[u] = n
            uniq.append((n, u))
    print("共 %d 条链接，去重后 %d 个待检\n" % (len(items), len(uniq)))

    results = []
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for r in ex.map(check, uniq):
            results.append(r)

    bad = [r for r in results if r[2] != "OK"]
    print("正常 %d 条，异常 %d 条\n" % (len(results) - len(bad), len(bad)))
    for name, url, st, msg in sorted(bad, key=lambda x: x[2]):
        print("  [%-6s] %-10s %-52s %s" % (st, name, url, msg))

    today = datetime.date.today().isoformat()
    L = ["# 校招官网链接体检报告\n", "> 生成于 %s ｜ 共检 %d 条，异常 %d 条\n" % (today, len(results), len(bad))]
    if bad:
        L.append("\n## 异常链接（需处理）\n")
        L.append("| 公司 | 链接 | 状态 | 说明 |")
        L.append("|---|---|---|---|")
        for name, url, st, msg in sorted(bad, key=lambda x: x[2]):
            L.append("| %s | %s | %s | %s |" % (name, url, st, msg))
    else:
        L.append("\n全部链接正常 ✅")
    L.append("\n## 说明\n")
    L.append("- **DNS失败**：域名解析不了，通常是子域名猜错或域名已废弃，必须改。")
    L.append("- **连接失败**：能解析但连不上，常见原因是品牌换新后旧域名被服务器拒绝，必须改。")
    L.append("- **空内容**：返回 200 但页面为空，多为站点反爬（需真实浏览器），需人工确认，不一定是死链。")
    io.open(REPORT, "w", encoding="utf-8").write("\n".join(L))
    print("\n报告已写入: %s" % REPORT)


if __name__ == "__main__":
    main()
