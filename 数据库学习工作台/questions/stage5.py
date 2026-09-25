# -*- coding: utf-8 -*-
"""阶段 5：窗口函数 —— TopN、并列排名、同环比、累计/移动窗口、占比"""

QUESTIONS = [
    {
        "id": "S5-Q01", "stage": 5, "title": "分组 TopN：各类销售额前 2 名", "difficulty": "medium", "points": 12,
        "prompt": """
找出**每个商品分类**里销售额最高的前 2 个商品：
- category_name、product_id、name、amount（销售额，保留 2 位）、rn（名次）
- 每个分类最多 2 行，按 category_name 升序、rn 升序
""",
        "hint": "窗口函数是最后计算的一层（在 GROUP BY 之后），所以要么用 CTE 先聚合再开窗，要么直接在同一层里把聚合放进 OVER 的 ORDER BY。",
        "verify": {"mode": "exact", "answer": """
WITH sales AS (
    SELECT c.name                            AS category_name,
           p.product_id,
           p.name,
           SUM(i.quantity * i.unit_price)    AS amount
    FROM order_items i
    JOIN products   p   ON p.product_id   = i.product_id
    JOIN categories c   ON c.category_id  = p.category_id
    GROUP BY c.name, p.product_id, p.name
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY category_name ORDER BY amount DESC) AS rn
    FROM sales
)
SELECT category_name, product_id, name, ROUND(amount, 2) AS amount, rn
FROM ranked
WHERE rn <= 2
ORDER BY category_name, rn;
"""},
        "teach": """
**为什么不能一步到位**：窗口函数在逻辑执行顺序里排在 GROUP BY / 聚合之后，
却排在 ORDER BY 之前。所以「先聚合，再对聚合结果开窗」必须分两层，用 CTE 表达最清楚。

```
FROM → WHERE → GROUP BY → 聚合 → 窗口函数 → ORDER BY → LIMIT
```

**ROW_NUMBER 的并列处理**：它对每个 peer 组给出 **1,2,3** 的连续编号，
即使金额完全相同也会强行分出先后。如果业务上并列就该共享名次，要用 RANK/DENSE_RANK（见 S5-Q02）。

MySQL 5.7 没有窗口函数，老版本的 TopN 要靠「用户变量模拟」或自连接 + COUNT 计数，
写出来很难维护 —— 这也是 MySQL 8 最重要的升级之一。
""",
    },
    {
        "id": "S5-Q02", "stage": 5, "title": "ROW_NUMBER / RANK / DENSE_RANK 的差异", "difficulty": "medium", "points": 12,
        "prompt": """
按**累计销量**给商品排名（含滞销品，销量记 0），返回前 30 行：
- product_id、name、sold_qty、rn（ROW_NUMBER）、rk（RANK）、drk（DENSE_RANK）
- 按 sold_qty 降序、product_id 升序；排名为依据 sold_qty 降序
- rn 需要加第二排序键 product_id 保证确定性
""",
        "hint": "同一句 OVER (ORDER BY sold_qty DESC) 上叠三个不同的窗口函数即可对比效果。注意窗口函数不能出现在 WHERE 里，要过滤排名必须再包一层 CTE。",
        "verify": {"mode": "exact", "answer": """
SELECT p.product_id,
       p.name,
       COALESCE(SUM(i.quantity), 0) AS sold_qty,
       ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(i.quantity), 0) DESC, p.product_id) AS rn,
       RANK()       OVER (ORDER BY COALESCE(SUM(i.quantity), 0) DESC)               AS rk,
       DENSE_RANK() OVER (ORDER BY COALESCE(SUM(i.quantity), 0) DESC)               AS drk
FROM products p
LEFT JOIN order_items i ON i.product_id = p.product_id
GROUP BY p.product_id, p.name
ORDER BY rk, p.product_id
LIMIT 30;
"""},
        "teach": """
三种排名的区别，用数据说话：

| 销量 | ROW_NUMBER | RANK | DENSE_RANK |
|---|---|---|---|
| 36 | 1 | 1 | 1 |
| 32 | 2 | 2 | 2 |
| 32 | 3 | 2 | 2 |
| 31 | 4 | **4** | **3** |

- `ROW_NUMBER()`：不管是否并列都给连续序号，**同一个 select 执行两次可能结果不同**（并列内部顺序未定义）。
  用于分页、去重取一条时必须加第二排序键，否则结果不确定。
- `RANK()`：并列后跳号（1,1,3），符合体育比赛规则。
- `DENSE_RANK()`：并列后不跳号（1,1,2），适合做分组内的等级。

**最常见的错误**：把排名过滤写在同一层的 WHERE 里 ——
`WHERE ROW_NUMBER() OVER (...) = 1` 是语法错误，因为窗口函数在 WHERE 之后才计算。
必须包一层 CTE 或派生表。
""",
    },
    {
        "id": "S5-Q03", "stage": 5, "title": "LAG/LEAD 计算环比", "difficulty": "medium", "points": 12,
        "prompt": """
按月份算出 GMV 的**环比**：
- ym、gmv（本月 GMV，不含已取消，保留 2 位）
- prev_gmv：上个月的 GMV（首月为 NULL）
- mom_pct：环比增长率 = (本月 - 上月) / 上月 × 100，保留 2 位小数（首月为 NULL）
- 按 ym 升序，返回全部月份
""",
        "hint": "LAG(expr) OVER (ORDER BY ym) 取排在前面的那一行。要小心分母为上个月的 NULL 或 0。",
        "verify": {"mode": "exact", "answer": """
WITH monthly AS (
    SELECT STRFTIME('%Y-%m', created_at) AS ym,
           ROUND(SUM(total_amount), 2)   AS gmv
    FROM orders
    WHERE status <> 'cancelled'
    GROUP BY STRFTIME('%Y-%m', created_at)
)
SELECT ym,
       gmv,
       LAG(gmv) OVER (ORDER BY ym) AS prev_gmv,
       ROUND(100.0 * (gmv - LAG(gmv) OVER (ORDER BY ym))
             / NULLIF(LAG(gmv) OVER (ORDER BY ym), 0), 2) AS mom_pct
FROM monthly
ORDER BY ym;
"""},
        "teach": """
LAG / LEAD 让「行和行之间的比较」不再需要自连接，一次扫描搞定。

```sql
LAG(col)  OVER (ORDER BY x)        -- 上一行
LEAD(col) OVER (ORDER BY x)        -- 下一行
LAG(col, 3) OVER (ORDER BY x)      -- 往前 3 行
LAG(col, 1, 0) OVER (ORDER BY x)   -- 没有前一行时用 0 兜底（默认 NULL）
```

**必踩的坑：除零**。首月没有上月数据，LAG 返回 NULL，整个表达式变成 NULL —— 这是对的。
但如果上个月 GMV 恰好是 0，`/ 0` 在 SQLite 里结果 NULL，在 PostgreSQL 里却直接报错
`division by zero`。统一用 `NULLIF(分母, 0)` 或 `CASE WHEN 分母 <> 0 THEN ... END` 防御。

另一个坑：**不要在 ORDER BY 里直接引用窗口函数的别名参与除法**（如927），
标准做法是像上面那样重复写表达式，或者用 CTE 多一层。
""",
    },
    {
        "id": "S5-Q04", "stage": 5, "title": "累计求和 SUM() OVER", "difficulty": "medium", "points": 10,
        "prompt": """
按月份输出 GMV 的**累计值**（running total）：
- ym、gmv、running_total（从第一个月累加到当前月，保留 2 位）
- 按 ym 升序
""",
        "hint": "SUM(gmv) OVER (ORDER BY ym ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)。ROWS 模式以物理行为界，RANGE 模式以值为界。",
        "verify": {"mode": "exact", "answer": """
WITH monthly AS (
    SELECT STRFTIME('%Y-%m', created_at) AS ym,
           ROUND(SUM(total_amount), 2)   AS gmv
    FROM orders
    WHERE status <> 'cancelled'
    GROUP BY STRFTIME('%Y-%m', created_at)
)
SELECT ym,
       gmv,
       SUM(gmv) OVER (ORDER BY ym
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM monthly
ORDER BY ym;
"""},
        "teach": """
**ROWS 与 RANGE 的区别**（面试高频）：

- `ROWS`：按物理行数算窗口边界。`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`
  永远是「当前行 + 前两行」共 3 行。
- `RANGE`：按 ORDER BY 列的**值**算边界。同样是 2 PRECEDING，
  RANGE 的含义是「值落在 [当前值-2, 当前值] 内的所有行」——
  **并列的行会被一起算进来**，行数不固定。

所以 RANGE 只对等差点（数值型）才有意义；对日期这类不均匀的数据，
想要「近 7 天」应该用 `RANGE BETWEEN INTERVAL '7 days' PRECEDING`（PostgreSQL）
而不是行数。SQLite 不支持 RANGE 的 INTERVAL 语法，MySQL 8 支持。

遗漏了 ORDER BY 时，`SUM(x) OVER ()` 的窗口是整个结果集，每行都得到同样的一行总和 ——
这正是 S5-Q07 算占比的基础。
""",
    },
    {
        "id": "S5-Q05", "stage": 5, "title": "移动平均（近 3 月）", "difficulty": "hard", "points": 12,
        "prompt": """
按月份计算 GMV 的**近 3 个月移动平均**（含当月）：
- ym、gmv、ma3（当月与前两月的均值，不足 3 个月时按已有月份平均，保留 2 位）
- 按 ym 升序
""",
        "hint": "AVG(gmv) OVER (ORDER BY ym ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) 即可；前几个月自然按实际行数平均。",
        "verify": {"mode": "exact", "answer": """
WITH monthly AS (
    SELECT STRFTIME('%Y-%m', created_at) AS ym,
           ROUND(SUM(total_amount), 2)   AS gmv
    FROM orders
    WHERE status <> 'cancelled'
    GROUP BY STRFTIME('%Y-%m', created_at)
)
SELECT ym,
       gmv,
       ROUND(AVG(gmv) OVER (ORDER BY ym
                            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS ma3
FROM monthly
ORDER BY ym;
"""},
        "teach": """
移动平均是消除季节波动最朴素也最直接的手段。窗口写法的关键优势是
**只扫一遍数据**：数据库内部维护一个小队列，滑出一行的同时滑入一行。

用自连接实现同样的效果会写成：

```sql
SELECT a.ym, AVG(b.gmv)
FROM monthly a
JOIN monthly b ON b.ym BETWEEN <三个月前> AND a.ym
GROUP BY a.ym
```

复杂度从 O(n) 变成 O(n × 窗口宽度)，且日期算术很容易写错。

`2 PRECEDING` 这种等值的阈在面对**日期缺口**时是按"行数"滑动的：
如果 3 月完全没有订单，它会跳过 3 月、用更早期的月份补足。
要按真实日期范围滑动，得先用 S4-Q07 的日历表补零，或改用 RANGE + 日期差值。
""",
    },
    {
        "id": "S5-Q06", "stage": 5, "title": "取每组最新一条（去重首选）", "difficulty": "hard", "points": 12,
        "prompt": """
用窗口函数重写 S4-Q04：查出**每个客户最近一笔订单**
- customer_id、order_id、created_at、total_amount
- 按 customer_id 升序，每个客户有且只有一行（35 行）
""",
        "hint": "ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC, order_id DESC) = 1，再在外层 WHERE rn = 1 过滤。",
        "verify": {"mode": "exact", "answer": """
WITH ranked AS (
    SELECT customer_id,
           order_id,
           created_at,
           total_amount,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY created_at DESC, order_id DESC) AS rn
    FROM orders
)
SELECT customer_id, order_id, created_at, total_amount
FROM ranked
WHERE rn = 1
ORDER BY customer_id;
"""},
        "teach": """
这是窗口函数最高频的用途：**按某分组去重取一条**。比关联子查询高效（只扫一次表），
也比 `GROUP BY + MAX` 灵活（能带出整行任意列，而不是只能取个聚合值）。

对比三种写法的取舍：

| 写法 | 扫描次数 | 并列时 | 能否带出其它列 |
|---|---|---|---|
| 关联子查询 WHERE col = (SELECT MAX...) | 两次 | 返回多行 | 能 |
| GROUP BY + MAX | 一次 | 一行（任选） | **不能**（只得聚合值） |
| ROW_NUMBER() = 1 | 一次 | 一行（可控） | 能 ✅ |

**务必加第二排序键** `order_id DESC`：只有 created_at 一个排序键时，
同一秒的两笔订单谁排第 1 是未定义的，结果可能在两次执行间跳变。
如果业务上并列应该「都保留」，把 ROW_NUMBER 换成 RANK 并把过滤条件改成 `rk = 1`。
""",
    },
    {
        "id": "S5-Q07", "stage": 5, "title": "占比：一行算出各组占总额百分比", "difficulty": "hard", "points": 12,
        "prompt": """
统计每个商品分类的销售额及其**占全站的比例**：
- category_name、amount（保留 2 位）、pct（百分比，保留 2 位）
- 按 amount 降序
- 用一个窗口函数搞定总数，**不要**再写一遍 SUM 子查询
""",
        "hint": "在分组查询里，`SUM(SUM(x)) OVER ()` 这种嵌套聚合写法可以一次性拿到总和：内层 SUM 是分组聚合，外层 SUM() OVER () 是窗口聚合。",
        "verify": {"mode": "exact", "answer": """
SELECT c.name                                    AS category_name,
       ROUND(SUM(i.quantity * i.unit_price), 2)  AS amount,
       ROUND(100.0 * SUM(i.quantity * i.unit_price)
             / SUM(SUM(i.quantity * i.unit_price)) OVER (), 2) AS pct
FROM order_items i
JOIN products   p ON p.product_id  = i.product_id
JOIN categories c ON c.category_id = p.category_id
GROUP BY c.name
ORDER BY amount DESC;
"""},
        "teach": """
`SUM(SUM(x)) OVER ()` 看起来很怪，但它精确对应两层执行：

- 内层 `SUM(x)`：GROUP BY 的分组聚合，得到每组一个小计；
- 外层 `SUM(...) OVER ()`：对这些小计再做一次窗口聚合，**OVER () 没有 PARTITION/ORDER，
  窗口就是整个结果集**，于是每行都拿到同一个总计值。

可读性差一点，可以用 CTE 拆成两步，效果一样：

```sql
WITH agg AS (SELECT ... SUM(...) AS amount FROM ... GROUP BY ...)
SELECT *, ROUND(100.0 * amount / SUM(amount) OVER (), 2) AS pct FROM agg
```

这个套路同样适用于「每行占本组多少」—— 把 OVER () 换成 OVER (PARTITION BY 组)。

别忘了 `100.0`：整数除法会先截断再乘，得到一堆 0。
""",
    },
]
