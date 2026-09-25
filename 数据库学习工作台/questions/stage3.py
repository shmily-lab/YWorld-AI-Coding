# -*- coding: utf-8 -*-
"""阶段 3：多表连接 —— JOIN 类型、反连接、自连接、行数膨胀"""

QUESTIONS = [
    {
        "id": "S3-Q01", "stage": 3, "title": "显式 INNER JOIN 取关联字段", "difficulty": "easy", "points": 5,
        "prompt": """
列出订单及其下单客户的信息：
- order_id、customer_name（来自 customers.name）、city、status、created_at
- 只取前 10 条，按 order_id 升序
- **必须用显式 JOIN ... ON 语法**，不要写 `FROM orders o, customers c WHERE ...`
""",
        "hint": "连接条件写在 ON 里，过滤条件留在 WHERE 里，职责分开；一行只有一个作用。",
        "verify": {"mode": "exact", "answer": """
SELECT o.order_id,
       c.name    AS customer_name,
       c.city,
       o.status,
       o.created_at
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
ORDER BY o.order_id
LIMIT 10;
"""},
        "teach": """
**永远写显式 JOIN**。逗号式连接的三个致命问题：

1. 连接条件和过滤条件混在 WHERE 里，5 张表以上基本没人看得懂；
2. 忘了写连接条件时，不会报错，而是**静默产生笛卡尔积**（280 × 40 = 11200 行）；
3. 想改成 LEFT JOIN 时，SQL-92 之前的方言写法各家不一（Oracle 的 `(+)`、SQL Server 的 `*=`）。

驱动表的选择：优化器一般让小表做驱动表（这里是 customers 40 行 vs orders 280 行），
并对被驱动表的连接列用索引。这个选择可以用 EXPLAIN 验证（阶段 8）。
""",
    },
    {
        "id": "S3-Q02", "stage": 3, "title": "LEFT JOIN 保留左表全部行", "difficulty": "easy", "points": 5,
        "prompt": """
统计每个商品被买了多少次、总共多少件：
- product_id、name、sold_cnt（出现在几笔明细里）、sold_qty（累计件数，没销量的显示 0）
- **滞销商品（从未卖出过）也要出现在结果里**，共 24 行
- 按 sold_cnt 降序、product_id 升序
""",
        "hint": "LEFT JOIN 保留左表全部商品；SUM 遇全 NULL 会返回 NULL，用 COALESCE 兜底。",
        "verify": {"mode": "exact", "answer": """
SELECT p.product_id,
       p.name,
       COUNT(i.order_id)           AS sold_cnt,
       COALESCE(SUM(i.quantity), 0) AS sold_qty
FROM products p
LEFT JOIN order_items i ON i.product_id = p.product_id
GROUP BY p.product_id, p.name
ORDER BY sold_cnt DESC, p.product_id;
"""},
        "teach": """
LEFT JOIN 的语义：**左表每一行都必须出现在结果里**；右表匹配不上时补 NULL。

因此 COUNT / SUM 这类聚合必须同时处理两件事：
- 计数用右表的非空列（`COUNT(i.order_id)`），而不是 `COUNT(*)`；
- 求和结果套 `COALESCE(..., 0)`，因为 SUM 在"这一组全是 NULL"时会返回 NULL
  （注意：COUNT 返回 0，SUM/AVG 返回 NULL，两者行为不同）。

还有个隐蔽陷阱：如果在 WHERE 里写了 `AND i.quantity > 0`，LEFT JOIN 会**退化成 INNER JOIN** ——
因为那些补 NULL 的行在 WHERE 阶段被过滤掉了。想保留左表就要把条件挪到 ON 子句里。
""",
    },
    {
        "id": "S3-Q03", "stage": 3, "title": "反连接：从未下单的客户", "difficulty": "medium", "points": 8,
        "prompt": """
找出**从来没有下过任何订单**的客户：
- customer_id、name、city、registered_at
- 按 customer_id 升序（本题有 5 位这样的客户）
""",
        "hint": "标准写法是 LEFT JOIN + 右表主键 IS NULL；等价写法是 NOT EXISTS。两种都比 NOT IN 安全 —— NOT IN 遇到子查询里有 NULL 时结果会是空集。",
        "verify": {"mode": "exact", "answer": """
SELECT c.customer_id, c.name, c.city, c.registered_at
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL
ORDER BY c.customer_id;
"""},
        "teach": """
三种写法，性能相近但**正确性不同**：

```sql
-- ① LEFT JOIN + IS NULL：通用，推荐
FROM customers c LEFT JOIN orders o ON ... WHERE o.order_id IS NULL

-- ② NOT EXISTS：语义最直接，MySQL 会转成 anti-join，推荐
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)

-- ③ NOT IN：⚠️ 危险
WHERE c.customer_id NOT IN (SELECT o.customer_id FROM orders o)
```

为什么 ③ 危险：`x NOT IN (1, 2, NULL)` 会被展开为 `x<>1 AND x<>2 AND x<>NULL`，
最后一项是 NULL，导致整个表达式为 NULL 而非 TRUE，**一行都选不出来**。
只有子查询结果列**确认 NOT NULL** 时才敢用 NOT IN。

`SELECT 1` 里的 1 没有任何含义，优化器只看 EXISTS 是否返回行；写 `SELECT *` 也行。
""",
    },
    {
        "id": "S3-Q04", "stage": 3, "title": "四表连接的明细宽表", "difficulty": "medium", "points": 8,
        "prompt": """
把订单明细展开成可读的宽表：
- order_id、item_no、product_name、category_name、quantity、unit_price、line_amount（保留 2 位）
- 按 order_id、item_no 升序，取前 20 行
""",
        "hint": "明细表是事实中心的起点：order_items → orders / products → categories。连接顺序按这个血缘链写，可读性最好。",
        "verify": {"mode": "exact", "answer": """
SELECT i.order_id,
       i.item_no,
       p.name      AS product_name,
       cat.name    AS category_name,
       i.quantity,
       i.unit_price,
       ROUND(i.quantity * i.unit_price, 2) AS line_amount
FROM order_items i
JOIN orders     o   ON o.order_id    = i.order_id
JOIN products   p   ON p.product_id  = i.product_id
JOIN categories cat ON cat.category_id = p.category_id
ORDER BY i.order_id, i.item_no
LIMIT 20;
"""},
        "teach": """
连接方向要沿着**外键血缘**走：明细行 → 归属订单 → 商品 → 分类。
每条 JOIN 都对应一个明确的外键，读者能一眼看出数据的来路。

`line_amount` 这类派生金额**不要手工落库** —— 它由 quantity × unit_price 决定，
一旦落库就存在更新不一致的风险（改了明细却忘了改金额）。

要把它变成"列"，应该交给生成列（generated column），由数据库担保它永远等于最新计算结果：
```sql
ALTER TABLE order_items ADD COLUMN line_amount
  GENERATED ALWAYS AS (quantity * unit_price) STORED;
```
SQLite 3.31+、MySQL 5.7+ 都支持生成列，PostgreSQL 12+ 支持 `GENERATED ALWAYS AS ... STORED`。
""",
    },
    {
        "id": "S3-Q05", "stage": 3, "title": "自连接：员工与直属上级", "difficulty": "medium", "points": 8,
        "prompt": """
列出每位员工及其直属上级：
- emp_id、employee（员工姓名）、salary、manager_id、manager（上级姓名，CEO 显示为 '—'）
- 按 emp_id 升序，共 15 行
""",
        "hint": "同一张表起两个别名即可自连接；顶层人员 manager_id 是 NULL，所以要用 LEFT JOIN，否则 CEO 会从结果里消失。",
        "verify": {"mode": "exact", "answer": """
SELECT e.emp_id,
       e.name                  AS employee,
       e.salary,
       e.manager_id,
       COALESCE(m.name, '—')    AS manager
FROM employees e
LEFT JOIN employees m ON m.emp_id = e.manager_id
ORDER BY e.emp_id;
"""},
        "teach": """
自连接只有一个要点：**必须起别名**，否则 `employees JOIN employees` 里的同名列无法区分，
数据库会报 "ambiguous column name"。

这里的外键 `manager_id → emp_id` 指向自己，构成一棵树。树的根节点（CEO）manager_id 为 NULL，
用 INNER JOIN 会把 5 位部门负责人丢失，这就是典型的"连接类型选错导致数据悄悄变少"。

验证习惯：写自连接类查询时，先把左右两侧行数各 COUNT 一遍，对不上说明连接类型或条件有问题。

多层级（祖父、曾祖父）不能靠反复自连接，要用递归 CTE —— 见 S4-Q06。
""",
    },
    {
        "id": "S3-Q06", "stage": 3, "title": "行数膨胀：为什么 SUM 被放大了", "difficulty": "hard", "points": 12,
        "prompt": """
统计**未取消订单**的三个口径：
- order_cnt、amount_sum（保留 2 位）、item_qty（明细总件数）

注意：如果直接把 orders 和 order_items 连起来求和，`SUM(total_amount)` 会被**按明细行数放大**
（一笔含 3 条明细的订单，其金额会被加 3 次）。请写出不会被放大的正确版本。
""",
        "hint": "先把明细按 order_id 聚合到一行（每单一行），再与 orders 连接，保证连接后仍是「一单一行」。",
        "verify": {"mode": "exact", "answer": """
SELECT COUNT(*)                    AS order_cnt,
       ROUND(SUM(o.total_amount), 2) AS amount_sum,
       SUM(t.total_qty)            AS item_qty
FROM orders o
JOIN (SELECT order_id, SUM(quantity) AS total_qty
      FROM order_items
      GROUP BY order_id) t ON t.order_id = o.order_id
WHERE o.status <> 'cancelled';
"""},
        "teach": """
这是 SQL 里最贵的错误之一：**主子表连接后聚合被放大**，而且不会报错，
只会静悄悄给出一个偏大的数字，直到有人手工核对才发现。

根因是 JOIN 的中间结果粒度变了：

| 阶段 | 粒度 | 每单含 3 条明细时 |
|---|---|---|
| FROM orders | 一单一行 | total_amount × 1 |
| JOIN order_items | **一明细一行** | total_amount × 3 |

两条解决路线：

1. **先聚合再连接**（本题做法）—— 用派生表把子表压到与主表同粒度（一单一行）。
2. `COUNT(DISTINCT o.order_id)` / `SUM(DISTINCT ...)` —— 治标不治本，
   DISTINCT 要额外去重且 SUM(DISTINCT x) 会把"金额恰好相同的两笔"算成一笔，不能用。

自检技巧：放大后的错误结果往往是正确值的 2~4 倍，量级明显不对时优先怀疑 JOIN 粒度。
""",
    },
    {
        "id": "S3-Q07", "stage": 3, "title": "避免隐式笛卡尔积", "difficulty": "medium", "points": 8,
        "prompt": """
同事写了一行统计：
```sql
SELECT COUNT(*) FROM customers c, orders o, order_items i;
```
他说想数订单明细行数，但这个写法得到的是 40 × 280 × 564 的乘积。

请写出一条**能同时**给出四个口径且绝不产生笛卡尔积的 SQL：
- line_cnt：订单明细行数
- customer_cnt：涉及到的客户数（去重）
- product_cnt：涉及到的商品数（去重）
- amount_sum：订单金额合计（保留 2 位，**不能被明细行数放大**）
""",
        "hint": "明细表与订单表一对一连接不会膨胀；客户数/商品数用 COUNT(DISTINCT)；金额只在不重复的条件下求和，或者干脆分两步 GROUP BY。",
        "verify": {"mode": "exact", "answer": """
SELECT COUNT(*)                       AS line_cnt,
       COUNT(DISTINCT o.customer_id)  AS customer_cnt,
       COUNT(DISTINCT i.product_id)   AS product_cnt,
       ROUND((SELECT SUM(total_amount) FROM orders), 2) AS amount_sum
FROM orders o
JOIN order_items i ON i.order_id = o.order_id;
"""},
        "teach": """
`FROM customers c, orders o, order_items i` 没有任何连接条件，得到的是三表的笛卡尔积
（40 × 280 × 564 ≈ 630 万行），跑完还不报错。这是**不写显式 JOIN** 最典型的代价。

金额的坑在于它和明细不在一个粒度上：一旦 orders 与 order_items 连接，
orders 侧的行就被复制了 N 份，SUM 随之放大。本题用**标量子查询** `(SELECT SUM(...) FROM orders)`
把金额单独在不膨胀的粒度上算出来，再拼进结果 —— 因为子查询只返回一行一列，不会造成任何行复制。

判断"会不会放大"的心法：
**连接以后行数是否变化**。没变（一对一）→ 直接聚合安全；变了（一对多）→ 聚合前先降粒度。
""",
    },
]
