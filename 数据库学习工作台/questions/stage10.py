# -*- coding: utf-8 -*-
"""阶段 10：综合融合作战

这一阶段的题**不教新语法**，只做一件事：把前面多个阶段的知识点压进一道题里。
它们不在正常学习路径上，而是由复习引擎在前置阶段全部通过之后解锁推送
（见 engine/review.py 的 review_unlocked）。

每道题都标了 `requires`（前置阶段）与 `covers`（本题检验哪些知识点）。
"""

QUESTIONS = [
    {
        "id": "S10-Q01", "stage": 10, "kind": "review", "requires": [1, 2],
        "title": "融合复习①：客户结构体检", "difficulty": "medium", "points": 15,
        "covers": ["阶段1 的 NULL 处理", "阶段2 的条件聚合", "一行多口径"],
        "prompt": """
用**一条** SQL 输出一行客户健康度体检报告：
- total_cnt：客户总数
- city_unknown_cnt：城市未知（city 为 NULL）的客户数
- email_missing_cnt：没有邮箱的客户数
- vip3_cnt：vip_level >= 3 的客户数
- avg_vip：平均 VIP 等级，保留 2 位小数

这一步刻意把「阶段 1 的 NULL 判断」和「阶段 2 的条件聚合」压在一起。
思考：统计 NULL 行数，除了 `COUNT(*) - COUNT(col)`，还能怎么写？
""",
        "hint": "COUNT(col) 跳过 NULL，所以「缺失数 = 总数 - 非空数」。带条件的计数用 SUM(CASE WHEN ... THEN 1 ELSE 0 END)。",
        "verify": {"mode": "exact", "answer": """
SELECT COUNT(*)                                          AS total_cnt,
       COUNT(*) - COUNT(city)                            AS city_unknown_cnt,
       COUNT(*) - COUNT(email)                           AS email_missing_cnt,
       SUM(CASE WHEN vip_level >= 3 THEN 1 ELSE 0 END)   AS vip3_cnt,
       ROUND(AVG(vip_level), 2)                          AS avg_vip
FROM customers;
"""},
        "teach": """
**一行多口径**是报表 SQL 的典型形态，核心技巧就是：所有指标共享同一个 FROM 和 WHERE，
靠不同的聚合表达式区分口径。

几个变体写法：

```sql
-- 写法 A：相减法（本题）
COUNT(*) - COUNT(city)

-- 写法 B：SUM + CASE（跨库最稳，MySQL/PG 都能跑）
SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END)

-- 写法 C：PostgreSQL 专属的 FILTER
COUNT(*) FILTER (WHERE city IS NULL)

-- 写法 D：MySQL 的布尔简写（方言，别跨库用）
SUM(city IS NULL)
```

推荐 B：语义最直白，且**不会因为聚合函数对 NULL 的处理规则不同而踩坑** ——
比如 `AVG` 会忽略 NULL，但 `COUNT` 不会，混用时很容易算错分母。
""",
    },
    {
        "id": "S10-Q02", "stage": 10, "kind": "review", "requires": [2, 3],
        "title": "融合复习②：城市维度经营看板", "difficulty": "hard", "points": 20,
        "covers": ["LEFT JOIN 保留左表", "条件聚合", "NULL 兜底", "去重计数"],
        "prompt": """
做一张按城市汇总的看板，**每个城市一行**（城市未知归到「未知」）：
- city：城市名，NULL 显示为 '未知'
- customer_cnt：该城市的客户数
- ordered_cnt：其中**下过单**的客户数（去重）
- never_ordered_cnt：从没下过单的客户数
- valid_amount：该城市客户的有效订单金额合计（排除 cancelled），没有订单的城市显示 0，保留 2 位

按 valid_amount 降序、city 升序。
""",
        "hint": "customers 作左表 LEFT JOIN orders；「下过单的客户数」要用 COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN c.customer_id END)。",
        "verify": {"mode": "exact", "answer": """
SELECT COALESCE(c.city, '未知') AS city,
       COUNT(DISTINCT c.customer_id) AS customer_cnt,
       COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN c.customer_id END) AS ordered_cnt,
       COUNT(DISTINCT c.customer_id)
         - COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN c.customer_id END) AS never_ordered_cnt,
       ROUND(COALESCE(SUM(CASE WHEN o.status <> 'cancelled' THEN o.total_amount ELSE 0 END), 0), 2) AS valid_amount
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY COALESCE(c.city, '未知')
ORDER BY valid_amount DESC, city;
"""},
        "teach": """
这道题集合了阶段 2/3 里最容易出错的三件事：

**1. 去重计数必须 DISTINCT + CASE 组合**
JOIN 之后一个客户会出现 N 行（他有 N 笔订单）。`COUNT(c.customer_id)` 数的是行数不是人数。
正确姿势是 `COUNT(DISTINCT CASE WHEN 条件 THEN c.customer_id END)` ——
CASE 先把不符合的行变成 NULL，DISTINCT 去掉重复客户，COUNT 跳过 NULL。

**2. GROUP BY 要用表达式而不是列**
按 `c.city` 分组时 NULL 会自成一组，但显示成 NULL 不好看。
`GROUP BY COALESCE(c.city, '未知')` 让分组键和展示值一致 ——
**分组键写什么，就按什么聚合**，这是 SQL 的硬规则。

**3. LEFT JOIN 下的 SUM**
没下过单的客户那一行，`o.status` 是 NULL，`NULL <> 'cancelled'` 的结果是 NULL（不是 TRUE），
所以会走 ELSE 0 —— 这正是我们想要的。但同时也要 `COALESCE(SUM(...), 0)`，
因为某个城市可能一行有效数据都没有。
""",
    },
    {
        "id": "S10-Q03", "stage": 10, "kind": "review", "requires": [3, 4, 5],
        "title": "融合复习③：商品动销分析", "difficulty": "hard", "points": 25,
        "covers": ["反连接计数", "标量子查询", "CTE 分层", "窗口占比"],
        "prompt": """
给每个商品分类出一行动销分析：
- category_name
- product_cnt：该分类下的商品数
- sold_product_cnt：**至少卖出过一次**的商品数
- unsold_cnt：从未卖出的商品数
- amount：该分类销售额，保留 2 位
- pct：占全站销售额的百分比，保留 2 位（用窗口函数算总数，不要写子查询）
- top_price_product：该分类里**挂牌价最高**的商品名（并列时取 product_id 小的）

按 amount 降序。建议用 CTE 把「分类聚合」和「最终展示」分成两层。
""",
        "hint": "第一层 CTE：categories JOIN products LEFT JOIN order_items，按分类聚合。第二层：用 SUM(amount) OVER () 算总销售额，再用关联标量子查询取最高价商品名。",
        "verify": {"mode": "exact", "answer": """
WITH cat AS (
    SELECT c.category_id,
           c.name                            AS category_name,
           COUNT(DISTINCT p.product_id)      AS product_cnt,
           COUNT(DISTINCT CASE WHEN i.order_id IS NOT NULL THEN p.product_id END) AS sold_product_cnt,
           ROUND(COALESCE(SUM(i.quantity * i.unit_price), 0), 2) AS amount
    FROM categories c
    JOIN products p ON p.category_id = c.category_id
    LEFT JOIN order_items i ON i.product_id = p.product_id
    GROUP BY c.category_id, c.name
)
SELECT category_name,
       product_cnt,
       sold_product_cnt,
       product_cnt - sold_product_cnt AS unsold_cnt,
       amount,
       ROUND(100.0 * amount / SUM(amount) OVER (), 2) AS pct,
       (SELECT p2.name
        FROM products p2
        WHERE p2.category_id = cat.category_id
        ORDER BY p2.price DESC, p2.product_id
        LIMIT 1) AS top_price_product
FROM cat
ORDER BY amount DESC;
"""},
        "teach": """
这道题把三个阶段的招数串在了一起，值得逐层拆：

**第一层（CTE）：动销计数**
`COUNT(DISTINCT CASE WHEN i.order_id IS NOT NULL THEN p.product_id END)`
—— 这是「有匹配的才算数」的标准写法，也就是在聚合里做反连接的补集。
注意这里不能用 `COUNT(i.product_id)`，因为一个商品会出现在多笔明细里，会被重复计数。

**第二层：占比用窗口**
`SUM(amount) OVER ()` 把第一层算出的 5 个小计再总合计一次，
外层行每行都拿到同一个总数 —— 比再写一遍子查询干净得多（见 S5-Q07）。

**关联标量子查询**
`(SELECT p2.name FROM products p2 WHERE p2.category_id = cat.category_id ORDER BY ... LIMIT 1)`
引用了外层的 `cat.category_id`，所以每输出一行就执行一次。这里只有 5 个分类，
代价可以忽略；分类成千上万时就应该改写成窗口函数：
```sql
FIRST_VALUE(p.name) OVER (PARTITION BY 分类 ORDER BY p.price DESC)
```

**「并列取 product_id 小的」这句很重要**：没有第二排序键时，谁排第一是未定义的，
同一条 SQL 两次执行可能给出不同商品 —— 这类 bug 在生产上表现为「报表每次刷新都在变」。
""",
    },
    {
        "id": "S10-Q04", "stage": 10, "kind": "review", "requires": [4, 5],
        "title": "融合复习④：客户价值分层（RFM 雏形）", "difficulty": "hard", "points": 25,
        "covers": ["CTE 分步", "排名函数", "窗口占比", "CASE 分层"],
        "prompt": """
做一份客户价值榜（RFM 里的 M 维度）：
1. 先按客户汇总（**排除已取消订单**）：order_cnt、amount、last_order_at（最近一单时间）
2. 再给出：rk（按 amount 降序的 RANK 排名）、pct（占全站有效销售额的百分比，保留 2 位）
3. 最后分层：rk <= 5 为 '头部'，rk <= 15 为 '腰部'，其余为 '长尾'
4. 返回 customer_id、name、order_cnt、amount、last_order_at、rk、pct、tier
5. 按 rk 升序、customer_id 升序，只取前 15 名

建议用两层 CTE：第一层聚合成「每人一行」，第二层做排名与占比，最外层做分层。
""",
        "hint": "分层 CASE 要放在排名算出来之后，所以必须再包一层 —— 窗口函数不能在同一层 WHERE 里过滤，同理也不能在同一层的 CASE 里引用刚算出的别名。",
        "verify": {"mode": "exact", "answer": """
WITH agg AS (
    SELECT o.customer_id,
           COUNT(*)                      AS order_cnt,
           ROUND(SUM(o.total_amount), 2) AS amount,
           MAX(o.created_at)             AS last_order_at
    FROM orders o
    WHERE o.status <> 'cancelled'
    GROUP BY o.customer_id
),
ranked AS (
    SELECT a.customer_id,
           c.name,
           a.order_cnt,
           a.amount,
           a.last_order_at,
           RANK() OVER (ORDER BY a.amount DESC) AS rk,
           ROUND(100.0 * a.amount / SUM(a.amount) OVER (), 2) AS pct
    FROM agg a
    JOIN customers c ON c.customer_id = a.customer_id
)
SELECT customer_id, name, order_cnt, amount, last_order_at, rk, pct,
       CASE WHEN rk <= 5  THEN '头部'
            WHEN rk <= 15 THEN '腰部'
            ELSE '长尾'
       END AS tier
FROM ranked
ORDER BY rk, customer_id
LIMIT 15;
"""},
        "teach": """
**为什么要三层**：这是窗口函数最典型的「分层依赖」问题。

```
第一层 agg    : 行粒度是「一单一行」→ 压成「一人一行」（GROUP BY + 聚合）
第二层 ranked : 在「一人一行」上开窗算排名和占比（依赖第一层的结果）
第三层 最外层 : 在排名之上做 CASE 分层（依赖第二层的结果）
```

每一层都只能引用**已经算出来的东西**，这就是分层 CTE 存在的唯一理由。
试图把它们压成一层会遇到两个硬限制：

1. 窗口函数不能在同一层 SELECT 的 WHERE 里过滤；
2. 同一层 SELECT 里定义的别名，不能在同层的其它表达式里引用
   （SQLite/MySQL 允许在 ORDER BY/GROUP BY 里引用，但 WHERE 和 CASE 里不行）。

**RANK 而不是 ROW_NUMBER**：金额恰好相同的客户应该并列，用 ROW_NUMBER 会人为分出先后，
导致「头部/腰部」的边界每次刷新都在变。

**RFM 的另外两个维度怎么加**：R（Recency）用 `julianday('now') - julianday(last_order_at)`，
F（Frequency）就是这里的 order_cnt。三个维度各自分 1~5 档，再组合成 125 个客群，
这就是经典的 RFM 模型。
""",
    },
    {
        "id": "S10-Q05", "stage": 10, "kind": "review", "requires": [6],
        "title": "融合复习⑤：可交付的历史数据归档", "difficulty": "hard", "points": 25,
        "covers": ["INSERT SELECT", "主子表删除顺序", "表结构复制", "幂等归档"],
        "prompt": """
把 **2025 年创建且已取消** 的订单完整归档，要求一次做完、可重复检查：

1. 建表 `archive_2025_cancelled`，结构要与 `orders` 完全一致（含主键与 CHECK 约束）
2. 用 INSERT ... SELECT 把目标订单整行搬过去
3. 删除这些订单**以及它们的明细**（外键要求先删明细）
4. 最后输出一行核对报告：
   - archived_cnt：归档表里的行数
   - remaining_2025_cnt：orders 里 2025 年剩下的订单数
   - orphan_item_cnt：无归属订单的明细行数（应为 0）
""",
        "hint": "顺序：CREATE TABLE → INSERT SELECT → DELETE order_items（用 IN 定位）→ DELETE orders → 最后 SELECT 核对。CTAS 简写会丢主键，必须手写 CREATE TABLE。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='archive_2025_cancelled')
    THEN 'FAIL: 归档表不存在'
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='archive_2025_cancelled'
                   AND sql LIKE '%PRIMARY KEY%')
    THEN 'FAIL: 归档表缺少 PRIMARY KEY（CTAS 简写会丢掉它）'
  WHEN (SELECT COUNT(*) FROM archive_2025_cancelled)
       <> (SELECT COUNT(*) FROM base.orders
           WHERE status='cancelled' AND created_at < '2026-01-01')
    THEN 'FAIL: 归档行数与源数据不一致'
  WHEN EXISTS (SELECT 1 FROM archive_2025_cancelled a JOIN base.orders b USING(order_id)
               WHERE a.customer_id<>b.customer_id OR a.total_amount<>b.total_amount
                  OR a.created_at<>b.created_at OR a.status<>b.status)
    THEN 'FAIL: 归档数据与原始数据不一致'
  WHEN EXISTS (SELECT 1 FROM orders o
               WHERE o.status='cancelled' AND o.created_at < '2026-01-01')
    THEN 'FAIL: 源表里仍残留已归档的订单'
  WHEN EXISTS (SELECT 1 FROM order_items i
               WHERE i.order_id NOT IN (SELECT order_id FROM orders))
    THEN 'FAIL: 存在孤儿明细（要先删子表再删主表）'
  WHEN EXISTS (SELECT 1 FROM orders o JOIN base.orders b USING(order_id)
               WHERE NOT (b.status='cancelled' AND b.created_at < '2026-01-01')
                 AND (o.status<>b.status OR o.total_amount<>b.total_amount))
    THEN 'FAIL: 误删或误改了不该动的订单'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE TABLE archive_2025_cancelled (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    status       TEXT    NOT NULL CHECK (status IN ('pending','paid','shipped','completed','cancelled')),
    created_at   TEXT    NOT NULL,
    paid_at      TEXT,
    total_amount NUMERIC NOT NULL DEFAULT 0
);

INSERT INTO archive_2025_cancelled
SELECT * FROM orders
WHERE status = 'cancelled' AND created_at < '2026-01-01';

DELETE FROM order_items
WHERE order_id IN (SELECT order_id FROM archive_2025_cancelled);

DELETE FROM orders
WHERE status = 'cancelled' AND created_at < '2026-01-01';

SELECT (SELECT COUNT(*) FROM archive_2025_cancelled)  AS archived_cnt,
       (SELECT COUNT(*) FROM orders
        WHERE created_at < '2026-01-01')              AS remaining_2025_cnt,
       (SELECT COUNT(*) FROM order_items
        WHERE order_id NOT IN (SELECT order_id FROM orders)) AS orphan_item_cnt;
"""},
        "teach": """
这道题是 S6-Q03 + S6-Q06 的合体，外加一层「交付自检」。

**为什么要以「核对报告」收尾**：任何数据迁移都应该以可验证的结论结束，
而不是「跑完没报错就当成功」。三个数字缺一不可：

- `archived_cnt` 回答「搬了多少」—— 对不上说明筛选条件写错了；
- `remaining_2025_cnt` 回答「源表还剩多少」—— 用来确认没误删；
- `orphan_item_cnt` 回答「有没有留下垃圾」—— 必须恒为 0。

**顺序为什么不能变**：

```
INSERT SELECT（先有备份，才敢删）
    ↓
DELETE 子表（明细外键是 RESTRICT，不先删会挡住你）
    ↓
DELETE 主表
    ↓
核对（用数字证明，而不是凭感觉）
```

把「先备份再删」这个顺序反过来（先删后插）就是事故：一旦中间失败，数据就真的没了。
这也是为什么归档表必须**显式 CREATE TABLE** —— CTAS 简写 `CREATE TABLE t AS SELECT ...`
会悄悄丢掉主键、索引、约束和默认值，看起来能跑，实际埋雷。

最后提醒：大表归档要分批（每批 5000 行以内）并在业务低峰执行。
""",
    },
    {
        "id": "S10-Q06", "stage": 10, "kind": "review", "requires": [8, 9],
        "title": "融合复习⑥：给分页接口配一套索引", "difficulty": "hard", "points": 25,
        "covers": ["联合索引", "排序方向", "覆盖索引", "避免临时排序"],
        "prompt": """
有个高频分页接口：

```sql
SELECT order_id, customer_id, created_at, total_amount
FROM orders
WHERE customer_id = 7
ORDER BY created_at DESC
LIMIT 20;
```

现在它得先扫全表、再排序、最后取 20 行。

请提交一组语句：
1. 创建索引 `idx_orders_cust_created_desc ON orders(customer_id, created_at DESC)`
   —— 注意第二列显式写 `DESC`，让它与 ORDER BY 的方向完全一致
2. 最后写上面那条 SELECT（就这四列，不要 SELECT *）

判分依据：执行计划里必须用到这个索引，且不能出现临时排序（TEMP B-TREE）。
""",
        "hint": "等值列在前、排序列在后；排序列的方向要和 ORDER BY 一致，否则引擎仍需额外排序。只 SELECT 索引里有的列（外加 rowid）还能顺带变成覆盖索引。",
        "verify": {"mode": "plan",
                   "contains": ["idx_orders_cust_created_desc"],
                   "not_contains": ["TEMP B-TREE"],
                   "answer": """
CREATE INDEX idx_orders_cust_created_desc ON orders(customer_id, created_at DESC);

SELECT order_id, customer_id, created_at, total_amount
FROM orders
WHERE customer_id = 7
ORDER BY created_at DESC
LIMIT 20;
"""},
        "teach": """
这道题把阶段 8 的两条规则和阶段 9 的实践串起来了。

**规则一：等值列在前，排序列在后**
`WHERE customer_id = 7` 是等值匹配，`ORDER BY created_at` 是排序，
所以索引必须写成 `(customer_id, created_at)`。反过来 `(created_at, customer_id)` 时，
优化器只能拿它做全索引扫描，再对 customer_id 过滤。

**规则二：方向必须一致**
普通索引每列默认 ASC。`ORDER BY created_at DESC` 需要反着走索引，
SQLite 会额外排一次序（计划里出现 `USE TEMP B-TREE FOR ORDER BY`），
MySQL 8 / PostgreSQL 则能反向扫描索引而不排序。
**在索引定义里显式写 `created_at DESC`** 是最稳的做法 ——
MySQL 8 和 PostgreSQL 都支持混合方向索引，SQLite 也认这个语法。

**规则三：只取需要的列**
`SELECT *` 会强制回表读全部列。这里只取四列，
如果把它们都放进索引（order_id 是 rowid，天然在索引里），
计划会变成 `USING COVERING INDEX`，连回表都省掉。

**组合起来的收益**：

| 方案 | 代价 |
|---|---|
| 无索引 | 扫 280 行 + 排序 + 截断 |
| 有索引 | 在 (7, 最新) 处定位，顺序读 20 个叶子节点，够数即停 |

数据量涨到千万行时，前者是几十秒，后者仍是毫秒级 —— 而且**与表大小基本无关**。
这就是「用写放大换读加速」最划算的一笔交易。
""",
    },
]
