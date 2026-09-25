# -*- coding: utf-8 -*-
"""阶段 1：查询基础 —— 投影、过滤、排序、NULL 语义、CASE、字符串/日期函数"""

QUESTIONS = [
    {
        "id": "S1-Q01", "stage": 1, "title": "投影、过滤、排序与分页", "difficulty": "easy", "points": 5,
        "prompt": """
查出所有 **已完成** 的订单：
- 返回列：order_id、customer_id、status、total_amount
- 过滤：status = 'completed'
- 排序：金额从高到低
- 只取前 10 条

> 注意 status 是区分大小写的字符串，CHECK 约束保证它全为小写。
""",
        "hint": "SELECT 列 -> FROM 表 -> WHERE 过滤 -> ORDER BY 排序 -> LIMIT 取条数，子句顺序固定，写错就是语法错。",
        "verify": {"mode": "exact", "answer": """
SELECT order_id, customer_id, status, total_amount
FROM orders
WHERE status = 'completed'
ORDER BY total_amount DESC
LIMIT 10;
"""},
        "teach": """
**执行顺序与书写顺序是两回事**：书写是 SELECT→FROM→WHERE→ORDER BY→LIMIT，
但逻辑执行是 FROM→WHERE→SELECT→ORDER BY→LIMIT。

这条 SQL 只能用 idx_orders_created 之类无关索引，实际会先全表扫 orders 再排序，
所以 LIMIT 10 **不能**减少扫描量，只减少返回量 —— 这是深分页问题的起点（阶段 9 展开）。
""",
    },
    {
        "id": "S1-Q02", "stage": 1, "title": "DISTINCT 去重的真实含义", "difficulty": "easy", "points": 5,
        "prompt": """
统计 customers 表里一共出现过哪些城市：
- 忽略城市未知（NULL）的客户
- 城市名去重
- 按 city 升序返回，列名就叫 city
""",
        "hint": "DISTINCT 作用于整个 SELECT 列表的组合，不是只作用于紧跟它的那一列。要排除 NULL 用 IS NULL / IS NOT NULL，千万别写 city != NULL。",
        "verify": {"mode": "exact", "answer": """
SELECT DISTINCT city
FROM customers
WHERE city IS NOT NULL
ORDER BY city;
"""},
        "teach": """
三个必踩的坑：

1. `city = NULL` 永远返回 unknown（不是 true 也不是 false），所以既不会被选中也不会!=掉。
   判断 NULL 只能用 `IS NULL` / `IS NOT NULL`。
2. `DISTINCT` 是对**整行**去重，写 `SELECT DISTINCT city, vip_level` 得到的是城市+等级的组合去重结果，
   行数会比只 DISTINCT city 多。
3. 如果你发现去重后行数远超预期，先怀疑是不是多列 DISTINCT。
""",
    },
    {
        "id": "S1-Q03", "stage": 1, "title": "COUNT 三种写法的差别", "difficulty": "easy", "points": 5,
        "prompt": """
用 **一条** SQL 回答三个问题，返回一行三列：
- total_cnt：customers 表的总行数
- has_email_cnt：email 不为空的客户数
- no_email_cnt：email 为空的客户数
""",
        "hint": "COUNT(列名) 会跳过该列为 NULL 的行；COUNT(*) 统计所有行。两者相减就是 NULL 行数。",
        "verify": {"mode": "exact", "answer": """
SELECT COUNT(*)                    AS total_cnt,
       COUNT(email)                AS has_email_cnt,
       COUNT(*) - COUNT(email)     AS no_email_cnt
FROM customers;
"""},
        "teach": """
`COUNT(*)` 数的是行，`COUNT(col)` 数的是 col 非 NULL 的行，`COUNT(DISTINCT col)` 数的是去重后的非 NULL 值。
这三者的差异常被误当成"数据库算错了"。

补充：`COUNT(1)` 在 SQLite/MySQL 里与 `COUNT(*)` 完全等价，优化器会忽略这个常量表达式，
不存在某些老笔记里说的性能差异。
""",
    },
    {
        "id": "S1-Q04", "stage": 1, "title": "LIKE 模糊匹配与前导通配符", "difficulty": "easy", "points": 5,
        "prompt": """
找出商品名里含「机」字的商品，返回 name 与 price，按价格从高到低排序。
""",
        "hint": "SQLite 的 LIKE 对 ASCII 字符默认不区分大小写；中文不受影响。通配符只有 % （任意长度）和 _ （单个字符）。",
        "verify": {"mode": "exact", "answer": """
SELECT name, price
FROM products
WHERE name LIKE '%机%'
ORDER BY price DESC;
"""},
        "teach": """
`'%机%'` 的 **左边** 也有通配符，意味着匹配位置不确定，B-Tree 索引无法定位起点，
只能退化为全表扫描 —— 这是 LIKE 最常见的索引失效场景，也是为什么搜索场景要靠
全文索引（MySQL FULLTEXT / ES）而不是 LIKE。

反过来，`'机%'` 这个后导通配符在 MySQL/SQLite 的 B-Tree 索引上是**可以**走范围扫描的。
""",
    },
    {
        "id": "S1-Q05", "stage": 1, "title": "日期范围的边界写法", "difficulty": "easy", "points": 8,
        "prompt": """
统计 **2026 年上半年**（含 2026-01-01，含 2026-06-30 全天）创建的订单：
- order_cnt：订单数
- amount_sum：金额合计，保留 2 位小数

要求用**半开区间** `>= 起点 AND < 终点` 来写，不要用 BETWEEN '2026-01-01' 到 '2026-06-30 23:59:59'。
""",
        "hint": "created_at 是 'YYYY-MM-DD HH:MM:SS' 的文本，可以直接做字符串比较。终点写成 '2026-07-01' 配 < 号。",
        "verify": {"mode": "exact", "answer": """
SELECT COUNT(*)                  AS order_cnt,
       ROUND(SUM(total_amount), 2) AS amount_sum
FROM orders
WHERE created_at >= '2026-01-01'
  AND created_at < '2026-07-01';
"""},
        "teach": """
**为什么不用 BETWEEN 到 23:59:59**：
1. 如果将来字段改成带毫秒或 TIMESTAMP(6)，23:59:59 会漏掉当天最后 1 秒的数据 —— 静默出错，最难排查。
2. `BETWEEN` 是闭区间，在 MySQL 里对 DATE 类型还会隐式补 00:00:00，跨类型的行为不一致。

**半开区间 `[start, next)` 是所有语言里处理区间的通用范式**（Python 切片、Java 的 subList 都是这个约定）。
而且它还有一个额外好处：放在列上进行纯比较，`created_at` 上的索引可用；若写成
`WHERE DATE(created_at) BETWEEN ...` 就把索引废掉了（见阶段 8）。
""",
    },
    {
        "id": "S1-Q06", "stage": 1, "title": "CASE WHEN 做数据打标", "difficulty": "medium", "points": 8,
        "prompt": """
给大额订单做金额分层，返回 order_id、total_amount、amount_level：
- total_amount >= 8000  → '超大额'
- 5000 <= total_amount < 8000 → '大额'
- 其余（前提是 > 3000）→ '较大额'

只统计 total_amount > 3000 的订单，按金额从高到低排序。
""",
        "hint": "CASE 是从上到下短路匹配，第一个满足的分支生效，所以分支顺序要从严到宽。别忘了 ELSE，否则不满足条件时返回 NULL。",
        "verify": {"mode": "exact", "answer": """
SELECT order_id,
       total_amount,
       CASE WHEN total_amount >= 8000 THEN '超大额'
            WHEN total_amount >= 5000 THEN '大额'
            ELSE '较大额'
       END AS amount_level
FROM orders
WHERE total_amount > 3000
ORDER BY total_amount DESC;
"""},
        "teach": """
CASE 有两种写法，别混：

```sql
CASE amount_level WHEN 'A' THEN 1 END   -- 简单 CASE，只能做等值比较，NULL 永远不匹配
CASE WHEN total_amount > 8000 THEN ...  -- 搜索 CASE，能写布尔表达式，日常用的都是这个
```

**短路特性**使得第二个分支能省掉 `total_amount < 8000` 这个条件 —— 第一个分支不满足时
自然意味着 amount < 8000。反过来写在前面的分支会"吃掉"后面的区间。
""",
    },
    {
        "id": "S1-Q07", "stage": 1, "title": "COALESCE 兜底与字符串提取", "difficulty": "medium", "points": 8,
        "prompt": """
整理客户联系方式，返回 customer_id、name、city、email_domain 四列，按 customer_id 升序：
- city 为 NULL 时显示 '未知'
- email_domain 取邮箱 @ 后面的部分；没有邮箱的客户显示 '-'
""",
        "hint": "SQLite 里取子串用 SUBSTR(串, 起点)，找位置用 INSTR(串, 子串)，字符串索引从 1 开始。MySQL 对应 SUBSTRING_INDEX(email,'@',-1)，PostgreSQL 对应 SPLIT_PART(email,'@',2)。",
        "verify": {"mode": "exact", "answer": """
SELECT customer_id,
       name,
       COALESCE(city, '未知') AS city,
       CASE WHEN email IS NULL THEN '-'
            ELSE SUBSTR(email, INSTR(email, '@') + 1)
       END AS email_domain
FROM customers
ORDER BY customer_id;
"""},
        "teach": """
`COALESCE(a, b, c)` 返回第一个非 NULL 的值，**短路求值**，是处理可空列显示的标准动作。
注意别用 `IFNULL`（MySQL 方言）或 `NVL`（Oracle 方言），COALESCE 才是 SQL 标准，且支持多参数。

另一个坑：`CONCAT(a, b)` 在 SQLite 里没有，要用 `||`。而且字符串拼接遇 NULL 就会整体变 NULL，
所以 `"'" || city || "'"` 在 city 为 NULL 时结果是 NULL 而不是 "''" —— 拼接前先 COALESCE。
""",
    },
    {
        "id": "S1-Q08", "stage": 1, "title": "多列排序与 NULL 的排序位置", "difficulty": "medium", "points": 8,
        "prompt": """
列出 VIP 等级最高的 20 位客户，返回 customer_id、name、city、vip_level、registered_at：
- 先按 vip_level 降序
- vip_level 相同时，城市未知的客户排在**最后**
- 再按注册时间升序
""",
        "hint": "SQLite 3.30+ 支持 ORDER BY city NULLS LAST。MySQL 没这个语法，要靠表达式排序：ORDER BY city IS NULL, city（IS NULL 返回 0/1，0 排前面）。",
        "verify": {"mode": "exact", "answer": """
SELECT customer_id, name, city, vip_level, registered_at
FROM customers
ORDER BY vip_level DESC, city NULLS LAST, registered_at ASC
LIMIT 20;
"""},
        "teach": """
NULL 在排序里的位置：**标准做法是 ASC 时排最前、DESC 时排最后**（SQLite 默认如此）。
但 MySQL 反过来 — SQLite/SQL Server 把 NULL 当作最小值，MySQL/Oracle 在 ASC 时也把 NULL 放最前。
跨库迁移时这个差异会直接改变报表顺序，所以显式写 `NULLS LAST`（SQLite/PostgreSQL/Oracle 支持）
或 `ORDER BY col IS NULL, col`（全库通用）更稳。

再看 `ORDER BY registered_at` 这一层：因为前两层已基本唯一，它只在同分同城的极端情况下生效，
但**必须写出来**才能保证结果确定性 —— 否则同一条 SQL 两次执行可能返回不同的 20 行，
这在分页场景里就是"翻页时数据重复/丢失"的经典 bug。
""",
    },
]
