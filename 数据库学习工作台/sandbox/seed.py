# -*- coding: utf-8 -*-
"""
确定性生成沙箱数据。同一份随机种子 => 同一份数据 => 答案可复现。

用法：
    python sandbox/seed.py            # 重建 sandbox/learn.db
"""
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import db  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "schema.sql")
DB = os.path.join(HERE, "learn.db")

SEED = 20260925
rng = random.Random(SEED)

# 观察基准日：所有题目里的绝对日期都围绕它设计
TODAY = datetime(2026, 9, 25)

CATEGORIES = [
    (1, "手机数码"), (2, "家用电器"), (3, "图书文娱"),
    (4, "服饰鞋包"), (5, "食品生鲜"),
]

PRODUCTS = [
    # (id, 名称, 分类, 挂牌价, 库存, 上架日期)
    (101, "Nova 手机 Pro", 1, 4299.00, 120, "2025-03-11"),
    (102, "Nova 手机 青春版", 1, 1899.00, 300, "2025-03-11"),
    (103, "无线降噪耳机", 1, 899.00, 450, "2025-05-02"),
    (104, "快充充电头 65W", 1, 129.00, 800, "2025-05-02"),
    (105, "智能手表 S3", 1, 1588.00, 60, "2025-09-18"),
    (106, "平板电脑 Air", 1, 3299.00, 45, "2026-01-20"),
    (107, "变频空调 1.5匹", 2, 2799.00, 80, "2025-04-08"),
    (108, "滚筒洗衣机 10kg", 2, 2199.00, 55, "2025-04-08"),
    (109, "双门冰箱 452L", 2, 3499.00, 30, "2025-06-15"),
    (110, "扫地机器人 T2", 2, 1999.00, 0, "2025-10-01"),
    (111, "电饭煲 4L", 2, 399.00, 500, "2026-02-14"),
    (112, "SQL 必知必会", 3, 59.00, 1000, "2025-01-05"),
    (113, "高性能 MySQL", 3, 128.00, 400, "2025-01-05"),
    (114, "数据密集型应用系统设计", 3, 139.00, 260, "2025-07-21"),
    (115, "数据库系统概念", 3, 158.00, 180, "2026-03-09"),
    (116, "胶片机套装", 3, 2680.00, 12, "2026-05-30"),
    (117, "纯棉短袖 T 恤", 4, 89.00, 900, "2025-02-20"),
    (118, "轻薄羽绒服", 4, 599.00, 220, "2025-11-11"),
    (119, "通勤双肩包", 4, 259.00, 350, "2025-11-11"),
    (120, "缓震跑鞋 V4", 4, 499.00, 0, "2026-04-02"),
    (121, "羊毛针织帽", 4, 129.00, 640, "2026-04-02"),
    (122, "云南小粒咖啡豆", 5, 108.00, 700, "2025-08-08"),
    (123, "智利车厘子 2斤", 5, 158.00, 150, "2025-12-01"),
    (124, "有机山茶油 1L", 5, 188.00, 300, "2026-06-06"),
]

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
SURNAME = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
GIVEN = ["嘉宁", "思远", "雨桐", "子墨", "若曦", "皓宇", "知微", "亦辰", "沐辰", "书言",
         "云舒", "清和", "景行", "砚青", "未晞", "向晚", "疏影", "望舒", "衔枝", "南风"]

STATUS_POOL = ["pending", "paid", "shipped", "completed", "cancelled"]
# 订单状态分布权重（completed 最多，pending 次之）
STATUS_W = [18, 22, 20, 32, 8]

# 116/121/124 是滞销新品：刻意不出现在任何订单里，用来练「反连接」写法
UNSOLD = {116, 121, 124}
SALABLE = [p for p in PRODUCTS if p[0] not in UNSOLD]

DEPARTMENTS = [(1, "技术中心"), (2, "供应链"), (3, "市场营销"), (4, "客户服务"), (5, "财务部")]

# 组织架构：emp_id, 姓名, 部门, 上级, 月薪
EMPLOYEES = [
    (1, "沈括", 1, None, 68000, "2019-04-01"),
    (2, "祖冲之", 1, 1, 42000, "2020-07-15"),
    (3, "李冶", 1, 1, 45000, "2020-09-01"),
    (4, "秦九韶", 1, 2, 28000, "2022-03-11"),
    (5, "杨辉", 1, 2, 26500, "2022-06-20"),
    (6, "刘徽", 1, 3, 30000, "2023-02-01"),
    (7, "赵爽", 1, 3, 24000, "2024-08-19"),
    (8, "墨翟", 2, None, 52000, "2019-09-09"),
    (9, "公输班", 2, 8, 31000, "2021-05-17"),
    (10, "计然", 3, None, 48000, "2020-01-06"),
    (11, "白圭", 3, 10, 29000, "2022-11-23"),
    (12, "范蠡", 4, None, 44000, "2021-02-14"),
    (13, "卜式", 4, 12, 21000, "2023-07-03"),
    (14, "桑弘羊", 5, None, 46000, "2020-03-30"),
    (15, "顾炎武", 5, 14, 22000, "2024-04-22"),
]


def rand_name(i):
    return SURNAME[i % len(SURNAME)] + GIVEN[(i // len(SURNAME)) % len(GIVEN)]


def rand_dt(start: datetime, end: datetime) -> datetime:
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, span))


def fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def build():
    # 原地重建：先把所有表 DROP 掉，避免依赖文件删除（受限沙箱会拦截 os.remove）
    db.wipe_all_tables(DB)
    con = sqlite3.connect(DB, isolation_level=None)
    con.executescript(open(SCHEMA, encoding="utf-8").read())
    cur = con.cursor()

    cur.executemany("INSERT INTO categories VALUES (?,?)", CATEGORIES)
    cur.executemany(
        "INSERT INTO products VALUES (?,?,?,?,?,?)",
        [(p[0], p[1], p[2], p[3], p[4], p[5] + " 09:00:00") for p in PRODUCTS],
    )
    cur.executemany("INSERT INTO departments VALUES (?,?)", DEPARTMENTS)
    cur.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)",
                    [(e[0], e[1], e[2], e[3], e[4], e[5] + " 09:00:00") for e in EMPLOYEES])

    # ---------- 客户：40 位，其中若干 city / email 为 NULL ----------
    customers = []
    reg_start = datetime(2024, 10, 1)
    for cid in range(1, 41):
        name = rand_name(cid)
        city = None if cid % 13 == 0 else CITIES[(cid * 3) % len(CITIES)]   # 3 位城市未知
        email = None if cid % 17 == 0 else f"user{cid:03d}@example.com"      # 2 位无邮箱
        vip = rng.choice([0, 0, 1, 1, 1, 2, 2, 3, 4, 5])
        reg = fmt(rand_dt(reg_start, datetime(2026, 8, 31)))
        customers.append((cid, name, city, email, vip, reg))
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", customers)

    # ---------- 订单：2025-01-01 ~ 2026-09-24 ----------
    orders = []
    items = []
    order_id = 10001
    order_start = datetime(2025, 1, 1)
    order_end = datetime(2026, 9, 24, 23, 0, 0)

    # 客户活跃度不同：前 6 位是高频复购用户，尾号 5 位从未下单（31~35 保持无订单）
    weights = []
    for cid in range(1, 41):
        if 31 <= cid <= 35:
            weights.append(0)
        elif cid <= 6:
            weights.append(10)
        else:
            weights.append(3)
    active_ids = [c for c, w in zip(range(1, 41), weights) if w > 0]

    while order_id <= 10280:
        cid = rng.choices(active_ids, weights=[weights[c - 1] for c in active_ids])[0]
        created = rand_dt(order_start, order_end)
        status = rng.choices(STATUS_POOL, weights=STATUS_W)[0]
        paid_at = None
        if status in ("paid", "shipped", "completed"):
            paid_at = fmt(created + timedelta(minutes=rng.randint(1, 60 * 36)))

        n_items = rng.choices([1, 2, 3, 4], weights=[35, 33, 22, 10])[0]
        picked = rng.sample(SALABLE, n_items)
        total = 0.0
        for idx, p in enumerate(picked, start=1):
            qty = rng.choices([1, 1, 1, 2, 3], weights=[62, 15, 10, 8, 5])[0]
            # 成交价在挂牌价基础上有 0~20% 折扣
            unit = round(p[3] * (1 - rng.choice([0, 0, 0.05, 0.1, 0.15, 0.2])), 2)
            items.append((order_id, idx, p[0], qty, unit))
            total += qty * unit
        orders.append((order_id, cid, status, fmt(created), paid_at, round(total, 2)))
        order_id += 1

    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)
    cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)

    # ---------- 反范式宽表：由正常数据展开而来 ----------
    flat = []
    for (oid, cid, status, created, _paid, _tot) in orders:
        cust = next(c for c in customers if c[0] == cid)
        for (o2, item_no, pid, qty, unit) in items:
            if o2 != oid:
                continue
            prod = next(p for p in PRODUCTS if p[0] == pid)
            cat = next(c for c in CATEGORIES if c[0] == prod[2])
            flat.append((len(flat) + 1, oid, cust[1], cust[2], cat[1], prod[1], qty, unit,
                         round(qty * unit, 2), created))
    cur.executemany("INSERT INTO order_flat VALUES (?,?,?,?,?,?,?,?,?,?)", flat)

    con.commit()
    con.close()
    print(f"[OK] 已生成 {DB}")
    print(f"     categories={len(CATEGORIES)} products={len(PRODUCTS)} departments={len(DEPARTMENTS)}")
    print(f"     employees={len(EMPLOYEES)} customers={len(customers)} orders={len(orders)} order_items={len(items)}")


if __name__ == "__main__":
    build()
