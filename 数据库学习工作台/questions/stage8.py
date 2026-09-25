# -*- coding: utf-8 -*-
"""阶段 8：索引与执行计划 —— plan 模式判分，断言直接落在 EXPLAIN QUERY PLAN 输出上"""

QUESTIONS = [
    {
        "id": "S8-Q01", "stage": 8, "title": "用单列索引消除全表扫描", "difficulty": "medium", "points": 10,
        "prompt": """
运营看板上有一个高频筛选：`SELECT * FROM orders WHERE status = 'cancelled'`。

现在 orders 表只有 customer_id 和 created_at 上的索引，这个查询只能全表扫
（`EXPLAIN QUERY PLAN` 会显示 `SCAN orders`）。

请提交**一组语句**：
1. 创建索引 `idx_orders_status ON orders(status)`
2. 最后写那条目标查询：`SELECT * FROM orders WHERE status = 'cancelled'`

判分依据：这条 SELECT 的计划里必须出现 `SEARCH orders USING INDEX idx_orders_status`，
并且不能再出现 `SCAN orders`。
""",
        "hint": "可以先单独跑 EXPLAIN QUERY PLAN 观察建索引前后的差别。记住要给最后一条 SELECT 单独存在。",
        "verify": {"mode": "plan",
                   "contains": ["SEARCH orders USING INDEX idx_orders_status"],
                   "not_contains": ["SCAN orders"],
                   "answer": """
CREATE INDEX idx_orders_status ON orders(status);

SELECT * FROM orders WHERE status = 'cancelled';
"""},
        "teach": """
SQLite 的计划术语很直观：

| 关键字 | 含义 |
|---|---|
| `SCAN 表` | 全表扫描，逐行读 |
| `SEARCH 表 USING INDEX idx (a=?)` | **索引查找**，直接用 B-Tree 定位 |
| `SCAN 表 USING INDEX idx` | 顺序遍历整个索引（比全表扫描快，但仍读了全部索引项） |
| `SEARCH 表 USING COVERING INDEX idx` | 索引本身已含全部需要的列，**无需回表** |
| `USE TEMP B-TREE FOR ORDER BY` | 需要在临时 B-Tree 里排序，纯属额外开销 |

所以要关注的不是"有没有 USING INDEX"，而是 **SEARCH 还是 SCAN**。
MySQL 的对应术语几乎一模一样（`type=ALL` 是全扫、`type=ref/range` 是索引查找），
PostgreSQL 则是 `Seq Scan` / `Index Scan` / `Index Only Scan`。

**为什么 status 这种低区分度列也值得建索引？** 看命中率：
如果必须返回 27% 的行，走索引反而会多一次回表。然而这里 cancelled 只占 8%，
索引过滤掉 92% 的行，收益远大于回表成本。是否建索引要看**谓词的选择性**而不是列的取值多少。
""",
    },
    {
        "id": "S8-Q02", "stage": 8, "title": "联合索引与最左前缀原则", "difficulty": "hard", "points": 15,
        "prompt": """
典型的「查某个客户某段时间的订单」场景。

请提交**一组语句**：
1. 创建联合索引 `idx_orders_customer_created ON orders(customer_id, created_at)`
2. 最后写一条能**同时用上两个索引列**的查询，例如查 customer_id = 3 且 2026 年之后创建的订单
   （返回 order_id、customer_id、created_at、total_amount）

判分依据：计划里必须出现 `SEARCH orders USING INDEX idx_orders_customer_created`，
并且要能看出 created_at 这一列也被用作了范围条件（`created_at>?` 或 `created_at<?`）。
""",
        "hint": "最左前缀：索引 (a,b,c) 只能「从最左边开始连续匹配」。WHERE 里要么用到 a，要么用到 a+b；只查 b 是不能用这棵树的。",
        "verify": {"mode": "plan",
                   "contains": ["SEARCH orders USING INDEX idx_orders_customer_created", "created_at>"],
                   "not_contains": ["SCAN orders"],
                   "answer": """
CREATE INDEX idx_orders_customer_created ON orders(customer_id, created_at);

SELECT order_id, customer_id, created_at, total_amount
FROM orders
WHERE customer_id = 3 AND created_at >= '2026-01-01';
"""},
        "teach": """
B-Tree 联合索引的物理结构是 **先按第一列排序，第一列相同时再按第二列排序**。
所以只有"给定左边的值"这个前缀，才能在这棵树上做二分定位 —— 这就是**最左前缀原则**。

以 `(customer_id, created_at)` 为例：

| WHERE 条件 | 能否用索引 | 用到哪些列 |
|---|---|---|
| `customer_id = 3` | 能 | customer_id |
| `customer_id = 3 AND created_at >= '2026-01-01'` | 能 | customer_id + created_at ✅ |
| `created_at >= '2026-01-01'` | **不能**（跳过最左列） | 退化为全表扫描 |
| `customer_id > 3 AND created_at = '2026-01-01'` | 部分能 | **遇到范围后，右边的列只能当过滤器用** |

最后一条最容易踩：范围之后断裂。所以**等值列放前面、范围列放后面**，
这条规则决定了联合索引的列顺序该怎么写。

另一个维度是**区分度**：`customer_id` 有 35 个取值，排在前面能迅速缩小行数。
设计索引时的经验顺序：等值列（区分度高者优先）→ 范围列 → 排序列。
""",
    },
    {
        "id": "S8-Q03", "stage": 8, "title": "覆盖索引：避免回表", "difficulty": "hard", "points": 15,
        "prompt": """
`SELECT AVG(price) FROM products WHERE category_id = 1` 现在走 `idx_products_category`，
命中行之后还要**回表**去读 price 列。

请提交**一组语句**：
1. 创建联合索引 `idx_products_cat_price ON products(category_id, price)`
2. 最后写那条 `SELECT AVG(price) FROM products WHERE category_id = 1`

判分依据：计划里必须出现 `SEARCH products USING COVERING INDEX idx_products_cat_price`。
""",
        "hint": "覆盖索引 = 查询需要的列全都在索引里，引擎不必再回主键树取行。注意 price 必须真的写在索引定义里。",
        "verify": {"mode": "plan",
                   "contains": ["SEARCH products USING COVERING INDEX idx_products_cat_price"],
                   "answer": """
CREATE INDEX idx_products_cat_price ON products(category_id, price);

SELECT AVG(price) FROM products WHERE category_id = 1;
"""},
        "teach": """
二级索引的叶子节点存的是「索引列 + 主键值」。所以用二级索引定位到一条记录后，
如果还要其它列，就得拿着主键**再回主键树查一次** —— 这就是**回表**（MySQL 的说法），
PostgreSQL 里对应 `Heap Fetches`，SQLite 则表现为计划里没有 COVERING 字样。

回表的代价：一次随机 IO。命中 1000 行就是 1000 次随机 IO。
这正是 MySQL 优化器有时**放弃索引直接全表扫描**的原因 ——
全表扫描是顺序 IO，当命中行数超过表总量的 20%~30%，可能反而更快。

覆盖索引把要用的列都塞进索引，让随机 IO 变成纯顺序扫索引叶子。它是**收益最大的
单点优化手段之一**，代价是索引变宽、写入变慢、占用更多磁盘。

PostgreSQL 的术语最直白：`Index Only Scan` 就是覆盖索引扫描。
MySQL 在 EXPLAIN 的 Extra 列里显示 `Using index`。
""",
    },
    {
        "id": "S8-Q04", "stage": 8, "title": "索引失效：函数包裹了列", "difficulty": "hard", "points": 15,
        "prompt": """
有人写了这条统计年度订单的 SQL：

```sql
SELECT COUNT(*) FROM orders WHERE STRFTIME('%Y', created_at) = '2026';
```

它的问题是 `created_at` 被 STRFTIME 函数包住了。跑 `EXPLAIN QUERY PLAN` 会发现
不是 `SEARCH` 而是 `SCAN orders USING COVERING INDEX idx_orders_created` —— 整棵索引被扫了一遍。

请提交一条**等价但如果正确的半开区间写法**（不含 DDL），用纯列比较而不对本列调用函数。
返回一列 COUNT(*)，别名为 cnt。
""",
        "hint": "把「年份等于 2026」翻译成「created_at >= '2026-01-01' AND created_at < '2027-01-01'」。这样列是裸的，索引可以做范围定位。",
        "verify": {"mode": "plan",
                   "contains": ["SEARCH orders", "idx_orders_created", "created_at>?", "created_at<?"],
                   "not_contains": ["SCAN orders"],
                   "answer": """
SELECT COUNT(*) AS cnt
FROM orders
WHERE created_at >= '2026-01-01'
  AND created_at <  '2027-01-01';
"""},
        "teach": """
**索引失效的四大原因**，背下来能挡掉绝大多数慢查询：

| 失效写法 | 原因 | 改写方向 |
|---|---|---|
| `WHERE 函数(列) = 值` | 索引存的是列原值，对算出来的东西无法二分 | 把函数移到常量侧 **`值 >= 列 AND 列 > 值`** |
| `WHERE 列 LIKE '%abc'` | 前导通配符导致无法确定扫描起点 | 改用后缀匹配 `abc%`，或上倒排/全文索引 |
| `WHERE 字符串列 = 123`（类型不匹配） | MySQL 会对**列**做隐式转换，等价于函数包裹 | 保证传入参数类型与列一致 |
| `WHERE a = 1 OR b = 2`（a、b 分别有单列索引） | 一棵索引树无法同时服务两个列的条件 | 改写成两条 SQL UNION ALL，或建合适的联合索引 |

**为什么函数包在常量侧就没关系**：`WHERE created_at < DATE('2026-01-01')` 里，
DATE() 的输入是常量，引擎会先算出结果再和列比较，所以索引仍然可用。

MySQL 8.0.13+ 和 PostgreSQL 支持**函数索引/表达式索引**来救这一类查询，
但代价是维护一份额外的表达式 B-Tree，且只对该表达式有效。能用范围条件改写时就别用。
""",
    },
    {
        "id": "S8-Q05", "stage": 8, "title": "让 ORDER BY 用上索引，告别临时排序", "difficulty": "hard", "points": 15,
        "prompt": """
分页组件要按 `(customer_id, created_at)` 排序输出：

```sql
SELECT order_id, customer_id, created_at
FROM orders
ORDER BY customer_id, created_at
LIMIT 10;
```

现在这张表上没有能满足这个排序的索引，`EXPLAIN QUERY PLAN` 会显示
`USE TEMP B-TREE FOR ORDER BY` —— 引擎要把全部 280 行读出来排序再取前 10 条。

请提交**一组语句**：
1. 创建联合索引 `idx_orders_sort ON orders(customer_id, created_at)`
2. 最后写上面那条 SELECT（只选 order_id、customer_id、created_at 三列）

判分依据：计划里不能再出现 `TEMP B-TREE`，并且要出现 `USING INDEX`。
""",
        "hint": "ORDER BY 的列顺序要与索引列顺序一致，且方向一致（全 ASC 或全 DESC），否则仍然要排序。",
        "verify": {"mode": "plan",
                   "contains": ["idx_orders_sort"],
                   "not_contains": ["TEMP B-TREE", "SCAN orders\n"],
                   "answer": """
CREATE INDEX idx_orders_sort ON orders(customer_id, created_at);

SELECT order_id, customer_id, created_at
FROM orders
ORDER BY customer_id, created_at
LIMIT 10;
"""},
        "teach": """
B-Tree 索引本身**有序**，所以 ORDER BY 只要顺着索引的叶子链表走就是天然排好序的，
一旦能用上，`USE TEMP B-TREE FOR ORDER BY` 就消失了。

用上索引排序的三个条件：

1. `ORDER BY` 的列顺序必须与索引列顺序一致（同样受最左前缀约束）；
2. **混合方向会失效**：索引默认 ASC，`ORDER BY a ASC, b DESC` 无法用，**除非**建成
   `(a ASC, b DESC)` 这种混合方向索引（MySQL 8 / PostgreSQL 支持，SQLite 不支持，会多排一次）；
3. `ORDER BY` 只能来自**同一张驱动表**，多表 JOIN 时排序列跨表就得建临时表排序。

还有一个常被忽略的点：**排序前的行来源**。即使建了索引，
如果 WHERE 里已经用上了别的索引定位行，优化器可能选择"按筛选索引取行 + 排序"，
而不是"按排序列索引取行 + 过滤"。这种情况下 MySQL 的 `Using filesort` 同样会出现，
需要用 `FORCE INDEX` 或改设计。

最后注意 `SELECT *` vs 只选索引列：本题只选三列且都在索引里（order_id 是 rowid），
所以计划是 `USING COVERING INDEX` —— 连回表都省了。
""",
    },
    {
        "id": "S8-Q06", "stage": 8, "title": "清理冗余索引", "difficulty": "hard", "points": 15,
        "prompt": """
索引不是免费的：每次 INSERT/UPDATE/DELETE 都要同步维护所有索引，
多余的索引会拖慢写入、占用磁盘、扰动优化器选错计划。

现有 orders 上的两个单列索引：`idx_orders_customer(customer_id)`、`idx_orders_created(created_at)`。
如果业务 95% 的查询形态是 `WHERE customer_id = ? AND created_at >= ?`，
其中 `idx_orders_customer` 就变成了**冗余索引** —— 它恰好是联合索引的最左前缀。

请提交一组语句：
1. 创建联合索引 `idx_orders_customer_created ON orders(customer_id, created_at)`
2. 删除冗余的 `idx_orders_customer`
3. **保留** `idx_orders_created`（按时间统计的查询仍然需要它）
""",
        "hint": "联合索引 (a, b) 天然可以当作 (a) 的索引使用，所以单独的 (a) 索引就没有独立价值了。但反过来，单独的 (b) 索引依然不可替代。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_orders_customer_created')
    THEN 'FAIL: 联合索引 idx_orders_customer_created 未创建'
  WHEN EXISTS (SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_orders_customer')
    THEN 'FAIL: idx_orders_customer 已成为联合索引的最左前缀，冗余应删除'
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_orders_created')
    THEN 'FAIL: 误删了 idx_orders_created，它是不可替代的'
  WHEN (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_orders_%') > 4
    THEN 'FAIL: 索引数量偏多，检查一下是不是多建了'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE INDEX idx_orders_customer_created ON orders(customer_id, created_at);

DROP INDEX idx_orders_customer;
"""},
        "teach": """
**冗余索引的产生规律**：如果已经存在索引 `(a, b, c)`，那么单独的 `(a)`、`(a, b)`
都是冗余的 —— 因为前者能被后者完全覆盖（最左前缀）。
反过来 `(b)`、`(b, c)`、`(c)` 都不是冗余的。

索引的真实成本：

| 成本 | 说明 |
|---|---|
| 磁盘 | 每个二级索引都是一棵独立的 B-Tree，宽索引可能比表本身还大 |
| 写入 | 一次 INSERT 要更新 N 棵索引树；N 越大，写放大越严重 |
| 优化器 | 候选索引越多，选错计划的概率越高，且每次解析都要遍历候选 |
| 锁 | MySQL InnoDB 的二级索引更新会产生 gap lock 竞争 |

线上清理索引的正确姿势（**千万别一把 DROP**）：

1. 先查索引使用统计 —— MySQL 用 `sys.schema_unused_indexes` 或
   `performance_schema.table_io_waits_summary_by_index_usage`；PostgreSQL 用
   `pg_stat_user_indexes.idx_scan`。SQLite 没有这类统计，只能靠人工梳理业务 SQL。
2. 确认连续 N 周 `count_star = 0` 之后再动。
3. MySQL 8 支持 `ALTER TABLE ... ALTER INDEX idx INVISIBLE` 先软下线，
   观察一段时间没问题再真正 DROP —— 这一步能救命。
""",
    },
]
