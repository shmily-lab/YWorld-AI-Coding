# -*- coding: utf-8 -*-
"""阶段 9：调优实战 —— 深分页、COUNT 优化、去相关子查询、大排序"""

QUESTIONS = [
    {
        "id": "S9-Q01", "stage": 9, "title": "深分页：keyset 游标替代 OFFSET", "difficulty": "hard", "points": 15,
        "prompt": """
列表页往下翻页越来越慢，根因通常就是 `OFFSET`：

```sql
SELECT ... FROM orders ORDER BY created_at DESC, order_id DESC LIMIT 10 OFFSET 20000;
```

数据库必须先**生成丢弃**前面 20000 行，才返回后 10 行 —— 翻得越深越慢，代价线性增长。

改用 keyset（游标）分页：前端传来上一页最后一行的游标
`created_at = '2026-06-15 08:30:00'`、`order_id = 10300`。

请写出**不使用 OFFSET** 的下一页查询：
- 返回 order_id、customer_id、created_at、total_amount
- 按 created_at DESC、order_id DESC 排序
- 取 10 行
- 必须排除游标所在行本身
""",
        "hint": "SQLite 3.15+ 支持行值（元组）比较：`(created_at, order_id) < (游标created_at, 游标order_id)`，它等价于 `created_at < v OR (created_at = v AND order_id < id)` 但写法简洁得多，索引也更友好。",
        "verify": {"mode": "exact", "answer": """
SELECT order_id, customer_id, created_at, total_amount
FROM orders
WHERE (created_at, order_id) < ('2026-06-15 08:30:00', 10300)
ORDER BY created_at DESC, order_id DESC
LIMIT 10;
"""},
        "teach": """
**为什么游标的分页是 O(log n) 而 OFFSET 是 O(n)**：

。。钟恒使用 `LIMIT 10 OFFSET 20000` 时要先把前 20010 行读出来排好再扔掉 20000 行；
keyset 分页直接在 `(created_at, order_id)` 的 B-Tree 上从游标位置往后走 10 个叶子节点，
代价与页码无关。

要让它真的快，必须有一个与 ORDER BY 完全同序的索引：

```sql
CREATE INDEX idx_orders_cursor ON orders(created_at DESC, order_id DESC);
```

MySQL 8 / PostgreSQL 同样支持行值比较（`ROW(a,b) < ROW(x,y)`），
MySQL 5.7 里要展开写成 `a < x OR (a = x AND b < y)` 的形式。

keyset 分页的两个**局限**，选型时要说清楚：

1. **不能跳页**。没有第 N 页的概念，只能"下一页"。要解决跳页，可以给每一页维护
   起始游标（书签表），或者用"上一页最大值"缓存。
2. **排序键必须唯一**。否则游标不唯一会导致重复/丢失行 ——
   这就是为什么上面始终坚持 `(created_at, order_id)` 这个复合排序键。
""",
    },
    {
        "id": "S9-Q02", "stage": 9, "title": "COUNT 只走索引不回表", "difficulty": "medium", "points": 12,
        "prompt": """
「2026 年一共有多少笔订单？」这个 COUNT 每天被跑几千次。

请提交这条 COUNT 查询（返回一列，别名为 cnt），要求使用**半开区间**条件，
使其执行计划是 `SEARCH orders USING COVERING INDEX idx_orders_created`。
""",
        "hint": "COUNT(*) 不需要读任何具体列，只要确定行数。只要 WHERE 条件落在 created_at 索引上，引擎连表都不用回。",
        "verify": {"mode": "plan",
                   "contains": ["SEARCH orders USING COVERING INDEX idx_orders_created",
                                "created_at>?", "created_at<?"],
                   "answer": """
SELECT COUNT(*) AS cnt
FROM orders
WHERE created_at >= '2026-01-01'
  AND created_at <  '2027-01-01';
"""},
        "teach": """
COUNT 相关的三个常见误解：

1. **`COUNT(*)` 并不比 `COUNT(id)` 慢**，现代优化器会把它们优化成同一形态 ——
   因为 COUNT(*) 只是数行，连列都不需要读。"用 COUNT(1) 优化"是老 MySQL/ORACLE 的说法，
   现在没有任何收益，反而降低了可读性。
2. **`COUNT(col)` 会跳过 NULL**，语义不同。
3. **InnoDB 的 COUNT(*) 为什么慢**：因为 MVCC，同一时刻不同事务看到的行数不同，
   引擎必须真的在一致性视图里去数一遍。MyISAM 能在常数时间返回是因为它被制约了并发。
   这也是为什么 PostgreSQL 至今没有 count-only scan 缓存。

真正快的 COUNT 优化手段：

- 让它走**最小的二级索引**（本题的做法）：覆盖索引让每行只占很少字节，
  InnoDB 的 MVCC 判断也便宜得多。
- 数据量极大且允许近似值时，用 `SHOW TABLE STATUS`（MySQL）/ reltuples（PG）的估算值，
  或 `EXPLAIN` 返回的 rows 字段 —— 差几个数量级没关系时这招最省。
- 有明确固定的去重场景务必写成 `COUNT(DISTINCT col)` 而不是拿
  `COUNT(*)` 去对一个 GROUP BY 的子查询计数。
- 实时精确的大表 COUNT，只能上计数器表或物化—— 这是架构问题不是 SQL 问题。
""",
    },
    {
        "id": "S9-Q03", "stage": 9, "title": "用一次 JOIN+GROUP BY 替代相关子查询", "difficulty": "hard", "points": 15,
        "prompt": """
找出 **2026 年高价值活跃客户**：2026 年（created_at 在 2026 年内）下单、
且排除已取消订单后累计金额 **超过 15000** 的客户。

要求：**不要写相关子查询**（不要在外层每行的 SELECT 或 WHERE 里嵌套依赖外层的子查询），
用「一次 JOIN + 一次 GROUP BY」完成。

- 返回 customer_id、name、order_cnt、total_amount（保留 2 位）
- 按 total_amount 降序、customer_id 升序
""",
        "hint": "先把 orders 与 customers 按 customer_id 连接，WHERE 里放时间范围与状态，GROUP BY 后 HAVING 做金额阈值过滤。",
        "verify": {"mode": "exact", "answer": """
SELECT c.customer_id,
       c.name,
       COUNT(*)                      AS order_cnt,
       ROUND(SUM(o.total_amount), 2) AS total_amount
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
WHERE o.created_at >= '2026-01-01'
  AND o.created_at <  '2027-01-01'
  AND o.status <> 'cancelled'
GROUP BY c.customer_id, c.name
HAVING SUM(o.total_amount) > 15000
ORDER BY total_amount DESC, c.customer_id;
"""},
        "teach": """
相关子查询的问题在于**执行方式**：外层每返回一行，内层就要执行一次。
外层 40 个客户 → 内层跑 40 次扫描；外层 100 万客户 → 跑 100 万次。
这通常会退化成一个嵌套循环，在 MySQL 里的代价专职行列/classO(N×M)。

改写为 JOIN + GROUP BY 后，数据库一次把两张表 hash/merge 起来再分组，
复杂度变成 O(N+M)。这也是为什么 MySQL 的 optimizer 在 5.6 之后引入了
semi-join / derived-table 合并来自动改写部分相关子查询 —— **但覆盖不全**，
一旦子查询里带 `LIMIT`、聚合或不相关条件，优化器就只能老老实实逐行执行。

判断要不要手动改写的心法：看 `EXPLAIN` 里那条子查询是不是出现在 select_type 的
`DEPENDENT SUBQUERY`（MySQL）或在执行计划里出现 SubPlan 且带outer references（PG）。
是的话，就值得手动改写成 JOIN。

最后注意：改写完一定要**验数据**。聚合条件变了以后很容易多/少几行，
把新旧两条 SQL 的结果各 SELECT COUNT(*) 对一遍是基本动作。
""",
    },
    {
        "id": "S9-Q04", "stage": 9, "title": "给大排序建合适的索引", "difficulty": "hard", "points": 15,
        "prompt": """
排行榜 SQL：`SELECT order_id, customer_id, total_amount FROM orders
ORDER BY total_amount DESC LIMIT 5`

现在它需要把 280 行全读出来排序才知道前 5 名是谁（`SCAN orders` +
`USE TEMP B-TREE FOR ORDER BY`）。数据涨到千万行时这会变成灾难。

请提交一组语句：
1. 创建索引 `idx_orders_amount ON orders(total_amount)`（让引擎顺着索引直接拿到前 5 名）
2. 最后写上面那条 SELECT（只返回 order_id、customer_id、total_amount 三列）
""",
        "hint": "索引本身有序，顺着走就是天然排好的。另外把查询需要的列都放进索引（含 rowid 的 order_id）还能顺便变成覆盖索引。",
        "verify": {"mode": "plan",
                   "contains": ["idx_orders_amount"],
                   "not_contains": ["TEMP B-TREE", "SCAN orders\n"],
                   "answer": """
CREATE INDEX idx_orders_amount ON orders(total_amount);

SELECT order_id, customer_id, total_amount
FROM orders
ORDER BY total_amount DESC
LIMIT 5;
"""},
        "teach": """
这是 TOP-N 类查询的标准解法：**用有序索引替代排序**。

在有 `idx_orders_amount` 之后，引擎从索引的最右端（DESC）出发，
连续读 5 个叶子节点就够了 —— 不管表里是 280 行还是 2800 万行，
代价都几乎不变。这就是 `LIMIT` 真正发挥作用的前提：**先有能支撑排序顺序的索引**。

对比一下三种实现的量级：

| 方案 | 代价 | 说明 |
|---|---|---|
| 全表扫 + 排序取前 N | O(N log N) 时间 + O(N) 内存 | 数据翻倍，耗时翻倍还要多 |
| 索引有序扫描取前 N | O(log N + N) | **本章正确答案** |
| 应用层把全表拉回来排序 | O(N log N) + 网络传输全量数据 | 最糟，还会撑爆应用内存 |

**索引的额外收益**：如果 SELECT 的列全部包含在索引里（本题的 order_id 是 rowid、
customer_id 需要额外加入索引才会被覆盖），计划会变成 COVERING INDEX，
连回表都省了。追求极致时可以把 `idx_orders_amount` 建为
`(total_amount DESC, customer_id)`，让它同时满足排序与覆盖。

请务必意识到：这条索引也让 `INSERT/UPDATE/DELETE` 变慢了一点点。
索引的本质是**用写放大换读加速**，总账要算过才好下单。
""",
    },
]
