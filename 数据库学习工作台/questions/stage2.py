# -*- coding: utf-8 -*-
"""阶段 2：聚合与分组 —— GROUP BY 边界、HAVING、条件聚合、NULL 在聚合里的行为"""

QUESTIONS = [
    {
        "id": "S2-Q01", "stage": 2, "title": "每个客户的订单统计（含 0 单客户）", "difficulty": "medium", "points": 8,
        "prompt": """
统计每个客户下了多少单，**从没下过单的客户也要出现在结果里**（显示 0 单）：
- customer_id、name
- order_cnt：订单总数
- paid_cnt：已支付订单数（paid_at 不为空才计）

按 customer_id 升序。
""",
        "hint": "要从左表保留全部客户，就必须 LEFT JOIN；聚合时数的是右表的非空列（COUNT(o.order_id)），如果把 COUNT(*) 写在这里会得到错误的 1。",
        "verify": {"mode": "exact", "answer": """
SELECT c.customer_id,
       c.name,
       COUNT(o.order_id)   AS order_cnt,
       COUNT(o.paid_at)    AS paid_cnt
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
"""},
        "teach": """
**LEFT JOIN 里计数必须用右表的列**，这是新手第一道坎：

- LEFT JOIN 之后，没匹配上的客户仍然会保留一行，只是 orders 那侧的列全是 NULL。
- `COUNT(*)` 数的是"结果集的行"，这一行存在就记 1，于是 0 单客户被记成 1。
- `COUNT(o.order_id)` 数的是"非空值个数"，NULL 不计数，于是得到正确的 0。

同理 `COUNT(o.paid_at)` 天然实现了"带条件的计数"，比写 SUM(CASE WHEN...) 更短。
""",
    },
    {
        "id": "S2-Q02", "stage": 2, "title": "各状态订单的金额画像", "difficulty": "easy", "points": 5,
        "prompt": """
按订单状态分组统计：
- status、order_cnt、sum_amount、avg_amount、max_amount、min_amount
- 金额类字段一律 ROUND 到 2 位小数
- 按订单数从多到少排序
""",
        "hint": "聚合函数会忽略 NULL；AVG(x) 等价于 SUM(x)/COUNT(x)，分母只数非 NULL 的行。",
        "verify": {"mode": "exact", "answer": """
SELECT status,
       COUNT(*)                        AS order_cnt,
       ROUND(SUM(total_amount), 2)     AS sum_amount,
       ROUND(AVG(total_amount), 2)     AS avg_amount,
       ROUND(MAX(total_amount), 2)     AS max_amount,
       ROUND(MIN(total_amount), 2)     AS min_amount
FROM orders
GROUP BY status
ORDER BY order_cnt DESC;
"""},
        "teach": """
一条 GROUP BY 可以放多个聚合函数，且它们的计算是**单次扫描同一批分组行**完成的，
不会多次扫表 —— 不要以为 SUM/AVG/MAX 各算一遍就各扫一遍。

另外注意：`AVG(amount)` 分母排除了 NULL 行，如果业务上 NULL 应当按 0 参与平均，
必须写 `AVG(COALESCE(amount, 0))`，否则平均值会被"虚高"。
""",
    },
    {
        "id": "S2-Q03", "stage": 2, "title": "WHERE 与 HAVING 的分工", "difficulty": "medium", "points": 8,
        "prompt": """
找出「有效篮板客户」：
- 排除已取消（status = 'cancelled'）的订单后，订单数 >= 5
- 且其中至少有一笔已支付（paid_at 不为空）
- 返回 customer_id、order_cnt、sum_amount（保留 2 位）
- 按 order_cnt 降序、customer_id 升序
""",
        "hint": "过滤「原始行」用 WHERE（在分组前执行），过滤「分组后的结果」用 HAVING。把 status 条件写进 HAVING 也能跑，但扫的行更多、语义更难读。",
        "verify": {"mode": "exact", "answer": """
SELECT customer_id,
       COUNT(*)                    AS order_cnt,
       ROUND(SUM(total_amount), 2) AS sum_amount
FROM orders
WHERE status <> 'cancelled'
GROUP BY customer_id
HAVING COUNT(*) >= 5
   AND COUNT(paid_at) >= 1
ORDER BY order_cnt DESC, customer_id;
"""},
        "teach": """
执行顺序决定了该写在哪：

```
FROM → WHERE(逐行过滤) → GROUP BY → HAVING(逐组过滤) → SELECT → ORDER BY → LIMIT
```

**性能含义**：WHERE 在分组前砍掉行，参与分组的数据量直接变小；HAVING 是分组后再砍，
那些行已经参与过 Hash/排序了。所以同一个条件下推（push down）到 WHERE 是标准的优化动作。

**表达力差异**：HAVING 里可以写聚合条件（`COUNT(*) >= 5`），WHERE 里不行 ——
因为 WHERE 执行时聚合还没有结果。反过来，涉及单行列的判断原则上都应放 WHERE。
""",
    },
    {
        "id": "S2-Q04", "stage": 2, "title": "条件聚合：状态行转列", "difficulty": "medium", "points": 10,
        "prompt": """
把每个客户的状态分布做成一张宽表：
- customer_id、name
- pending_cnt、paid_cnt、shipped_cnt、completed_cnt、cancelled_cnt（均为整数，未出现的状态记 0）
- 按 customer_id 升序，共 40 行（含从未下单的客户）
""",
        "hint": "在 CASE 里输出 1/0 再 SUM；不要试图把字段过滤写进 WHERE，那会把其他状态的行提前砍掉。",
        "verify": {"mode": "exact", "answer": """
SELECT c.customer_id,
       c.name,
       SUM(CASE WHEN o.status = 'pending'   THEN 1 ELSE 0 END) AS pending_cnt,
       SUM(CASE WHEN o.status = 'paid'      THEN 1 ELSE 0 END) AS paid_cnt,
       SUM(CASE WHEN o.status = 'shipped'   THEN 1 ELSE 0 END) AS shipped_cnt,
       SUM(CASE WHEN o.status = 'completed' THEN 1 ELSE 0 END) AS completed_cnt,
       SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_cnt
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
"""},
        "teach": """
条件聚合是把长表转宽表的利器，典型场景是"一次分组算出多口径指标"。

最容易写错的一点是：**SUM(CASE...) 在没有匹配行时可能返回 NULL**（如果所有分支都落到 NULL）。
这里因为用了 `ELSE 0`，LEFT JOIN 产生的空订单行会贡献 0，所以从不下单的客户得到 0 而不是 NULL。
如果写成 `SUM(CASE WHEN status='paid' THEN 1 END)` 不带 ELSE，那些客户就会得到 NULL，
外层再套 COALESCE 补救：`COALESCE(SUM(...), 0)`。

MySQL 里还有专属简写 `SUM(status = 'paid')`（布尔自动转 1/0），但那是方言，跨库别用。
""",
    },
    {
        "id": "S2-Q05", "stage": 2, "title": "SELECT 列表与 GROUP BY 的对齐", "difficulty": "medium", "points": 8,
        "prompt": """
统计每个商品累计卖出的件数与销售额：
- product_id、name、sold_qty（无销量的显示 0）、sold_amount（保留 2 位，无销量显示 0）
- 按销售额降序、product_id 升序
- 必须保留全部 24 个商品

思考题：如果把 `p.name` 从 GROUP BY 里拿掉，为什么在 MySQL（开启
ONLY_FULL_GROUP_BY）会报错、在 SQLite 却给出了一个"随便挑"的名字？
""",
        "hint": "GROUP BY 要写全所有非聚合列。这里用 product_id + name 分组；聚合列全部体现在 SELECT 列表里。",
        "verify": {"mode": "exact", "answer": """
SELECT p.product_id,
       p.name,
       COALESCE(SUM(i.quantity), 0)                    AS sold_qty,
       ROUND(COALESCE(SUM(i.quantity * i.unit_price), 0), 2) AS sold_amount
FROM products p
LEFT JOIN order_items i ON i.product_id = p.product_id
GROUP BY p.product_id, p.name
ORDER BY sold_amount DESC, p.product_id;
"""},
        "teach": """
**标准 SQL 的硬约束**：出现在 SELECT 里、又不在聚合函数里的列，必须出现在 GROUP BY 中。

不同库的反应完全不同，这是最危险的差异：

| 数据库 | 行为 |
|---|---|
| MySQL 5.7+（ONLY_FULL_GROUP_BY 默认开） | 直接报 SQL 模式错误 |
| MySQL 5.6 / 关闭该模式 | **返回一个不确定的值**（同组任意一行的 c.name） |
| SQLite / PostgreSQL | SQLite 允许并任选一行；PostgreSQL 直接报错 |
| SQL Server | 报错 |

所以"在我机器上能跑"不代表结果正确。要么把所有非聚合列放进 GROUP BY，
要么用 ANY_VALUE / MAX 明确表达"随便哪个都行"。
""",
    },
    {
        "id": "S2-Q06", "stage": 2, "title": "复购率：一行 SQL 算多个口径", "difficulty": "hard", "points": 12,
        "prompt": """
用**一条** SQL 算出运营看板的四个指标（返回一行四列）：
- total_customers：客户总数
- ordered_customers：至少下过 1 单的客户数
- repeat_customers：至少下过 2 单的客户数
- repeat_rate：复购率 = repeat_customers / ordered_customers × 100，保留 2 位小数
""",
        "hint": "先用一个派生表算出每个客户的订单数，再在外层做二次聚合。窗口函数还没学到，这里刻意用派生表写。",
        "verify": {"mode": "exact", "answer": """
SELECT COUNT(*)                                            AS total_customers,
       SUM(CASE WHEN t.order_cnt >= 1 THEN 1 ELSE 0 END)   AS ordered_customers,
       SUM(CASE WHEN t.order_cnt >= 2 THEN 1 ELSE 0 END)   AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN t.order_cnt >= 2 THEN 1 ELSE 0 END)
             / SUM(CASE WHEN t.order_cnt >= 1 THEN 1 ELSE 0 END), 2) AS repeat_rate
FROM (SELECT c.customer_id,
             COUNT(o.order_id) AS order_cnt
      FROM customers c
      LEFT JOIN orders o ON o.customer_id = c.customer_id
      GROUP BY c.customer_id) t;
"""},
        "teach": """
注意里面的 `100.0`：SQLite/MySQL 里整数除法会**截断取整**，`x/y*100` 若分子分母都是整数，
中间结果就被截断了。写成 `100.0 * x / y` 才能触发浮点运算。

另一个写法坑：不要把两个 SUM 直接相除后忘了分母可能为 0 —— 空数据集下会得 division by zero
（SQLite 返回 NULL，MySQL 视 SQL_MODE 返回 NULL 或报错）。稳妥写法是
`CASE WHEN SUM(...) = 0 THEN 0 ELSE ... END` 或套 `NULLIF(SUM(...), 0)`。
""",
    },
    {
        "id": "S2-Q07", "stage": 2, "title": "按月聚合与分组表达式", "difficulty": "medium", "points": 8,
        "prompt": """
统计每个月的订单数与 GMV（不含已取消订单）：
- ym：形如 '2026-03' 的年月
- order_cnt、gmv（保留 2 位）
- 按 ym 升序，返回全部 21 个月
""",
        "hint": "SQLite 用 STRFTIME('%Y-%m', created_at) 截取年月；MySQL 是 DATE_FORMAT(created_at,'%Y-%m')，PostgreSQL 是 TO_CHAR(created_at,'YYYY-MM')。GROUP BY 后面要重复这个表达式（SQLite/MySQL 允许写别名，PostgreSQL 不允许）。",
        "verify": {"mode": "exact", "answer": """
SELECT STRFTIME('%Y-%m', created_at)  AS ym,
       COUNT(*)                       AS order_cnt,
       ROUND(SUM(total_amount), 2)    AS gmv
FROM orders
WHERE status <> 'cancelled'
GROUP BY STRFTIME('%Y-%m', created_at)
ORDER BY ym;
"""},
        "teach": """
**这里埋了一个性能炸弹**：`STRFTIME('%Y-%m', created_at)` 是作用在**列**上的函数。
数据库只能对 `created_at` 的原始值做索引查找，对 `函数(created_at)` 无能为力，
于是 `idx_orders_created` 直接失效，变成全表扫描 + 临时表分组。

两条改良路线（阶段 8 会动手验证）：

1. 改写为纯列的范围条件：`WHERE created_at >= '2026-01-01' AND created_at < '2026-02-01'`。
2. MySQL 5.7+/PostgreSQL 可以建**函数索引**（PostgreSQL 直接 `CREATE INDEX ON orders (date_trunc('month', created_at))`；
   MySQL 8.0.13+ 支持函数索引；MySQL 5.7 只能加一个生成列再建索引）。

这条 SQL 还有一个隐藏特性：**结果不包含没有订单的月份**。要补零得借助递归 CTE
生成日历表再 LEFT JOIN —— 见 S4-Q07。
""",
    },
]
