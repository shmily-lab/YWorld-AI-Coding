# -*- coding: utf-8 -*-
"""阶段 4：子查询与 CTE —— 标量子查询、EXISTS、派生表、递归 CTE"""

QUESTIONS = [
    {
        "id": "S4-Q01", "stage": 4, "title": "标量子查询作为动态阈值", "difficulty": "easy", "points": 8,
        "prompt": """
找出金额**高于全站平均订单金额**的订单：
- order_id、customer_id、total_amount
- 也顺便查出 avg_amount（全站平均，保留 2 位）
- 按 total_amount 降序，取前 20 条
""",
        "hint": "标量子查询返回一行一列，可以直接当成一个值比较。注意它不能返回多行，否则会报错。",
        "verify": {"mode": "exact", "answer": """
SELECT order_id,
       customer_id,
       total_amount,
       (SELECT ROUND(AVG(total_amount), 2) FROM orders) AS avg_amount
FROM orders
WHERE total_amount > (SELECT AVG(total_amount) FROM orders)
ORDER BY total_amount DESC
LIMIT 20;
"""},
        "teach": """
标量子查询（scalar subquery）的位置非常灵活：可以出现在 WHERE 的比较右侧，
也可以出现在 SELECT 列表里当成一个计算列（如本题第二列的 avg_amount）。

两条硬规则：

1. 必须返回**恰好一行一列**。返回 0 行时得到 NULL（于是 `> NULL` 恒为 unknown，一行都查不到）；
   返回多行会直接报 `subquery returns more than one row`（MySQL）/ `more than one row returned by a subquery`（PostgreSQL）。
2. 非关联标量子查询只**执行一次**，结果被缓存复用；不像写在 select 列表里就每行执行一遍。
   （关联子查询才是每行执行一次，见 S4-Q04。）
""",
    },
    {
        "id": "S4-Q02", "stage": 4, "title": "EXISTS 半连接去重", "difficulty": "medium", "points": 10,
        "prompt": """
找出**至少买过一件「手机数码」分类商品**的订单：
- order_id、customer_id、created_at、total_amount
- 一笔订单即使买了 5 件该类商品，也只能出现**一次**
- 按 order_id 升序，取前 30 条
""",
        "hint": " EXISTS 找到第一匹配就短路返回 true，天然去重，比 JOIN + DISTINCT 更早终止扫描。",
        "verify": {"mode": "exact", "answer": """
SELECT o.order_id, o.customer_id, o.created_at, o.total_amount
FROM orders o
WHERE EXISTS (SELECT 1
              FROM order_items i
              JOIN products p   ON p.product_id = i.product_id
              JOIN categories c ON c.category_id = p.category_id
              WHERE i.order_id = o.order_id
                AND c.name = '手机数码')
ORDER BY o.order_id
LIMIT 30;
"""},
        "teach": """
这个场景三种写法的结果一样，代价差很多：

| 写法 | 中间结果 | 特点 |
|---|---|---|
| `JOIN ... GROUP BY/DISTINCT` | 先放大到明细行再去重 | 做了一堆无用功 |
| `IN (子查询)` | 先物化子查询结果集合 | 结果集大时内存/磁盘临时表压力大 |
| `EXISTS (关联子查询)` | 找到一条就返回 | **短路**，通常最优 |

MySQL 会把 EXISTS/IN 优化成 semi-join，两者计划常常趋同；但语义上 EXISTS 更贴近
「存在与否」这个意图，而且当子查询可能含 NULL 时，EXISTS 比 IN 安全（S4-Q03）。

注意子查询里必须写 `WHERE i.order_id = o.order_id` 把它与外层关联起来，
少了这句就退化成「全站存在手机数码销量」→ 恒真，所有订单都会被返回。
""",
    },
    {
        "id": "S4-Q03", "stage": 4, "title": "NOT EXISTS 反连接与 NOT IN 陷阱", "difficulty": "hard", "points": 12,
        "prompt": """
找出**从未被任何订单买过**的商品（滞销品）：
- product_id、name、category_id、price、stock
- 按 product_id 升序（本题有 3 个）

请先想清楚：如果改用 `NOT IN (SELECT product_id FROM order_items)`，
在 order_items.product_id 可能为 NULL 的情况下会发生什么？
""",
        "hint": "反连接的两种安全写法：NOT EXISTS（关联子查询）或 LEFT JOIN ... IS NULL。不要用 NOT IN，除非你确定子查询列非空。",
        "verify": {"mode": "exact", "answer": """
SELECT p.product_id, p.name, p.category_id, p.price, p.stock
FROM products p
WHERE NOT EXISTS (SELECT 1
                  FROM order_items i
                  WHERE i.product_id = p.product_id)
ORDER BY p.product_id;
"""},
        "teach": """
**NOT IN 的 NULL 陷阱**（面试与线上事故高频）：

```sql
WHERE p.product_id NOT IN (SELECT product_id FROM order_items)
```

被逻辑展开为：`product_id <> v1 AND product_id <> v2 AND ... AND product_id <> NULL`。

在三值逻辑里 `<> NULL` 的结果是 **unknown**，`TRUE AND unknown` = unknown，
整个条件不可能为 TRUE，于是 **一行都查不出来**，而且不报错。
只要子查询的结果列允许 NULL，这个写法就是一颗定时炸弹 —— 今天是好的，
哪天有人往子表里插了一条 NULL 记录，报表突然全空。

安全做法二选一：
```sql
WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.product_id = p.product_id)  -- 推荐
-- 或显式排除 NULL：
WHERE p.product_id NOT IN (SELECT product_id FROM order_items WHERE product_id IS NOT NULL)
```
""",
    },
    {
        "id": "S4-Q04", "stage": 4, "title": "关联子查询取每组最新一条", "difficulty": "hard", "points": 12,
        "prompt": """
查出**每个客户最近一笔订单**的信息：
- customer_id、order_id、created_at、total_amount
- 只返回下过单的客户（本题 35 位），按 customer_id 升序
""",
        "hint": "在子查询里用 o2.customer_id = c.customer_id 与外层关联，对每个客户各算一次 MAX(created_at)。",
        "verify": {"mode": "exact", "answer": """
SELECT c.customer_id, o.order_id, o.created_at, o.total_amount
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
WHERE o.created_at = (SELECT MAX(o2.created_at)
                      FROM orders o2
                      WHERE o2.customer_id = c.customer_id)
ORDER BY c.customer_id;
"""},
        "teach": """
这是**关联子查询**：子查询引用了外层列 `c.customer_id`，因此每一行都要重新执行一次。
时间复杂度大致是 O(N × log N)，N 小时够用，N 大时应改用窗口函数（见 S5-Q06，扫描一次即可）。

两个易错点：

1. **可能出现并列**：如果同一客户在同一秒下了两单，`=` 会返回 2 行，结果行数比客户数多。
   业务上要么在比较里加第二排序键（如 `order_id`），要么用窗口函数 ROW_NUMBER 强制取一条。
2. `MAX(created_at)` 只能保证时间戳最大，不能保证对应的 order_id 最大；
   想要「最新且 id 最大」，用 `(created_at, order_id)` 的元组比较：
   `WHERE (o.created_at, o.order_id) = (SELECT ... ORDER BY created_at DESC, order_id DESC LIMIT 1)`
   （SQLite 3.15+ 支持行值比较；MySQL 也支持，PostgreSQL 用 ROW(...) 语法。）
""",
    },
    {
        "id": "S4-Q05", "stage": 4, "title": "派生表做二次聚合", "difficulty": "hard", "points": 12,
        "prompt": """
做客户价值分层看板：
1. 先按客户汇总出累计消费金额（排除已取消订单）
2. 再按金额分层：>= 20000 为 '高价值'，>= 8000 为 '中价值'，其余为 '长尾'
3. 返回 cust_level、cust_cnt、level_amount（保留 2 位）
4. 按 level_amount 降序
""",
        "hint": "内层派生表负责「每人一行」，外层负责按金额区间再做一次分组聚合。不要把分层 CASE 塞进第一层的 GROUP BY，那样只能按原始行聚合，得不到分层结果。",
        "verify": {"mode": "exact", "answer": """
SELECT CASE WHEN t.total_amount >= 20000 THEN '高价值'
            WHEN t.total_amount >= 8000  THEN '中价值'
            ELSE '长尾'
       END                           AS cust_level,
       COUNT(*)                      AS cust_cnt,
       ROUND(SUM(t.total_amount), 2) AS level_amount
FROM (SELECT customer_id,
             SUM(total_amount) AS total_amount
      FROM orders
      WHERE status <> 'cancelled'
      GROUP BY customer_id) t
GROUP BY cust_level
ORDER BY level_amount DESC;
"""},
        "teach": """
派生表（derived table）是「把查询的结果当表用」，核心用途就是**分层聚合**。

这里 `GROUP BY cust_level` 引用了 SELECT 的别名 —— SQLite 与 MySQL 允许，
PostgreSQL 也允许引用 SELECT 别名，但 SQL Server 不允许，那时就要把整个 CASE 表达式抄一遍，
或者再包一层 CTE。**跨库工程里用 CTE 更稳**（见 S4-Q06）。

这类写法还有个常见的变异：用 CTE 让每一步都有名字，代码审阅时能一眼看出
「第一层算出人的层级，第二层按层级汇总」，可读性远好于嵌套两层派生表。
""",
    },
    {
        "id": "S4-Q06", "stage": 4, "title": "CTE 分步与递归查询组织架构", "difficulty": "hard", "points": 15,
        "prompt": """
employees 表的 manager_id 自引用，形成一棵组织架构树。请用**递归 CTE** 把它展开：
- emp_id、name、level（CEO 为 1，逐级 +1）、path（上级链路，形如「沈括 > 祖冲之 > 秦九韶」）
- 按 path 升序返回全部 15 行
""",
        "hint": "WITH RECURSIVE 由两部分组成：锚成员（选出 manager_id IS NULL 的顶层）+ UNION ALL 递归成员（自己连自己）。递归成员里必须引用 CTE 自己的名字，并且要能逐步收敛。",
        "verify": {"mode": "exact", "answer": """
WITH RECURSIVE org(emp_id, name, manager_id, level, path) AS (
    SELECT emp_id, name, manager_id, 1, name
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.emp_id, e.name, e.manager_id, o.level + 1, o.path || ' > ' || e.name
    FROM employees e
    JOIN org o ON e.manager_id = o.emp_id
)
SELECT emp_id, name, level, path
FROM org
ORDER BY path;
"""},
        "teach": """
递归 CTE 的形式化结构：

```sql
WITH RECURSIVE cte_name(列清单) AS (
    锚成员 SELECT ...                    -- 起点
    UNION ALL
    递归成员 SELECT ... FROM cte_name ... -- 引用自身
)
SELECT * FROM cte_name;
```

四个必须记住的点：

1. **UNION ALL 而不是 UNION**：UNION 会去重，除了拖慢还可能把合法的重复路径干掉。
2. **必须能收敛**：每递归一层数据都要变少或变小，否则无限循环。
   SQLite 有 `PRAGMA cte_max_depth` 兜底；MySQL 8 对应 `cte_max_recursion_depth`（默认 1000）。
3. **`path` 列**是渲染树形菜单/面包屑的关键，也用来做 `ORDER BY path` 得到树的先序展示。
4. 循环引用（A 管 B、B 管 A）会造成死循环。生产库要么靠层级上限约束，要么在 path 里加
   「新节点不能已在 path 中」的判断。

MySQL 5.7 及以下没有 CTE —— 那里只能写存储过程或用邻接表 + 多次自连接。
""",
    },
    {
        "id": "S4-Q07", "stage": 4, "title": "递归生成日历表，为缺失月份补零", "difficulty": "hard", "points": 15,
        "prompt": """
上一阶段 S2-Q07 的结果里，"没有订单的月份"会整行消失，画折线图时会断。

请构造 2026 年 1 月到 9 月的**连续月份序列**，LEFT JOIN 上每月的 GMV（不含已取消订单）：
- ym、order_cnt（没有订单的月份显示 0）、gmv（显示 0）
- 按 ym 升序，必须返回 9 行
""",
        "hint": "用 WITH RECURSIVE 生成 ym 序列：锚成员从 '2026-01' 开始，递归成员用 DATE(ym || '-01', '+1 month') 推进，并用 ym < '2026-09' 终止。",
        "verify": {"mode": "exact", "answer": """
WITH RECURSIVE cal(ym) AS (
    SELECT '2026-01'
    UNION ALL
    SELECT STRFTIME('%Y-%m', DATE(ym || '-01', '+1 month'))
    FROM cal
    WHERE ym < '2026-09'
),
monthly AS (
    SELECT STRFTIME('%Y-%m', created_at) AS ym,
           COUNT(*)                      AS order_cnt,
           ROUND(SUM(total_amount), 2)   AS gmv
    FROM orders
    WHERE status <> 'cancelled'
      AND created_at >= '2026-01-01'
      AND created_at <  '2026-10-01'
    GROUP BY STRFTIME('%Y-%m', created_at)
)
SELECT c.ym,
       COALESCE(m.order_cnt, 0) AS order_cnt,
       COALESCE(m.gmv, 0)       AS gmv
FROM cal c
LEFT JOIN monthly m ON m.ym = c.ym
ORDER BY c.ym;
"""},
        "teach": """
**日期维度的缺失值补全**是报表类的刚需。思路永远是：

> 用「维度序列」做左表（因为它必须完整），用「聚合结果」做右表（它可能缺行）。

生产环境更推荐物化一张 `dim_date` 日历表（年/月/日/季度/是否工作日全部预计算好），
比每次递归生成更快，也方便 JOIN 多个事实表对齐口径。

另一个做法是把序列先生成到临时表或 CTE；这里用递归的好处是零维护成本。

注意 `DATE(ym || '-01', '+1 month')` 利用了 SQLite 的修饰符语法；
MySQL 是 `DATE_ADD(CONCAT(ym,'-01'), INTERVAL 1 MONTH)`，PostgreSQL 是
`(ym || '-01')::date + INTERVAL '1 month'`。
""",
    },
]
