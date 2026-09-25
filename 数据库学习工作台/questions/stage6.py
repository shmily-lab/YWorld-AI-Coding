# -*- coding: utf-8 -*-
"""阶段 6：数据变更与事务 —— INSERT/UPDATE/DELETE/UPSERT、事务原子性、数据归档

本阶段的判分方式全部是 check 模式：
先执行你提交的 SQL，再执行一段校验 SQL。校验端可以同时访问
    main.*  —— 你改过之后的数据
    base.*  —— 未被污染的原始基准库
因此可以做「逐行比对」级别的精确判定。
"""

QUESTIONS = [
    {
        "id": "S6-Q01", "stage": 6, "title": "INSERT：主外键的顺序", "difficulty": "easy", "points": 8,
        "prompt": """
新增一位客户和他的一笔订单（两条 INSERT 组成的一组语句）：

客户：
- name = '陈默'，city = '武汉'，email = 'chenmo@example.com'
- vip_level = 3，registered_at = '2026-09-25 10:00:00'
- customer_id 由数据库自动生成（INSERT 时不要写这一列）

订单：
- order_id = 99001，属于上面刚插入的客户（不能写死 customer_id 数字）
- status = 'pending'，created_at = '2026-09-25 10:05:00'，paid_at = NULL
- total_amount = 599.00
""",
        "hint": "先插主表再插子表；子表要引用 newly generated 的主键值，用标量子查询 (SELECT customer_id FROM customers WHERE email='chenmo@example.com') 更安全，不要猜自增id。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN (SELECT COUNT(*) FROM customers) <> (SELECT COUNT(*) FROM base.customers) + 1
    THEN 'FAIL: 客户总数不是基准+1，检查是否多插或漏插'
  WHEN NOT EXISTS (SELECT 1 FROM customers
                   WHERE name='陈默' AND city='武汉' AND email='chenmo@example.com'
                     AND vip_level=3 AND registered_at='2026-09-25 10:00:00')
    THEN 'FAIL: 新客户字段值不符合要求'
  WHEN (SELECT COUNT(*) FROM orders) <> (SELECT COUNT(*) FROM base.orders) + 1
    THEN 'FAIL: 订单总数不是基准+1'
  WHEN NOT EXISTS (SELECT 1 FROM orders o JOIN customers c ON c.customer_id=o.customer_id
                   WHERE o.order_id=99001 AND c.email='chenmo@example.com'
                     AND o.status='pending' AND o.paid_at IS NULL
                     AND o.created_at='2026-09-25 10:05:00' AND o.total_amount=599.00)
    THEN 'FAIL: 新订单没有正确关联到新客户，或字段值不对'
  ELSE 'PASS'
END
""",
        "answer": """
INSERT INTO customers(name, city, email, vip_level, registered_at)
VALUES ('陈默', '武汉', 'chenmo@example.com', 3, '2026-09-25 10:00:00');

INSERT INTO orders(order_id, customer_id, status, created_at, paid_at, total_amount)
VALUES (99001,
        (SELECT customer_id FROM customers WHERE email = 'chenmo@example.com'),
        'pending', '2026-09-25 10:05:00', NULL, 599.00);
"""},
        "teach": """
**三条变更铁律**：

1. **先 SELECT 再改**。任何 UPDATE/DELETE 之前，用**完全相同的 WHERE** 先跑一遍
   `SELECT COUNT(*)` 确认影响行数。这一步能拦掉 90% 的线上误删。
2. **主外键顺序**。插入先主表后子表；删除反过来先子表后主表。
   外键约束打开时（`PRAGMA foreign_keys=ON`，MySQL 里默认 ON）顺序错了会直接报错，
   这正是外键的价值 —— 把错误拦在执行前而不是修复数据之后。
3. **不要猜自增 id**。用 `INSERT ... VALUES` 让数据库生成主键后，
   子表引用应该靠标量子查询或 `last_insert_rowid()`（SQLite）/`LAST_INSERT_ID()`（MySQL）；
   写死的 id 在并发或多环境部署时必错。

批量插入请写成 `INSERT INTO t VALUES (..),(..),(..)` 一条语句，
而不是循环执行 1000 条 INSERT —— 后者每条都要走一次事务提交，慢一个数量级。
""",
    },
    {
        "id": "S6-Q02", "stage": 6, "title": "UPDATE ... FROM 关联更新回填冗余字段", "difficulty": "medium", "points": 12,
        "prompt": """
orders.total_amount 是与明细冗余的字段，怀疑存在与实际明细金额不一致的情况。

请用**一条 UPDATE** 把所有订单的 total_amount 按 order_items 重新计算并回填：
- 新值 = ROUND(SUM(quantity * unit_price), 2)
- 只更新存在明细的订单
- 用 UPDATE ... FROM 语法（不要写逐行的关联子查询）
""",
        "hint": "SQLite 3.33+ / PostgreSQL 用 UPDATE ... FROM；MySQL 的语法是 UPDATE t1 JOIN t2 ON ... SET ...。三者都能完成同一件事，但写法完全不同。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN EXISTS (SELECT 1
               FROM orders o
               WHERE o.total_amount <> ROUND((SELECT SUM(quantity*unit_price)
                                              FROM base.order_items
                                              WHERE order_id = o.order_id), 2))
    THEN 'FAIL: 仍有订单的金额与明细重新计算的结果不一致'
  WHEN EXISTS (SELECT 1 FROM orders o JOIN base.orders b USING(order_id)
               WHERE o.status<>b.status OR o.created_at<>b.created_at)
    THEN 'FAIL: 除了金额以外，不应该改动其它列'
  ELSE 'PASS'
END
""",
        "answer": """
UPDATE orders
SET total_amount = ROUND(src.amt, 2)
FROM (SELECT order_id, SUM(quantity * unit_price) AS amt
      FROM order_items
      GROUP BY order_id) src
WHERE src.order_id = orders.order_id;
"""},
        "teach": """
这就是**跨库差异最大**的一条语句：

```sql
-- SQLite 3.33+ / PostgreSQL / SQL Server（用 MERGE）
UPDATE orders
SET total_amount = ROUND(src.amt, 2)
FROM (SELECT order_id, SUM(quantity*unit_price) AS amt
      FROM order_items GROUP BY order_id) src
WHERE src.order_id = orders.order_id;

-- MySQL
UPDATE orders o
JOIN (SELECT order_id, SUM(quantity*unit_price) AS amt
      FROM order_items GROUP BY order_id) src ON src.order_id = o.order_id
SET o.total_amount = ROUND(src.amt, 2);
```

注意 MySQL 的 `SET` 必须**放在 JOIN 之后**，位置与标准 SQL 相反。

还有两个通用陷阱：

- **UPDATE 忘记 WHERE 就是全表更新**。养成「先 SELECT COUNT(*) 用同样的 JOIN 和 WHERE」的习惯。
- MySQL 在 safe-updates 模式下（`SQL_SAFE_UPDATES=1`）会拒绝没有用索引列的 UPDATE/DELETE，
  这是个救命开关，生产环境建议打开。
""",
    },
    {
        "id": "S6-Q03", "stage": 6, "title": "DELETE：主子表级联删除", "difficulty": "medium", "points": 12,
        "prompt": """
清理历史数据：删除 **2025 年创建且已取消** 的订单，以及它们的所有明细。

要求：
- 先从子表 order_items 删，再从主表 orders 删（外键约束要求这个顺序）
- 不能误删其它订单，也不能留下没有归属订单的孤儿明细
""",
        "hint": "删除条件要同时满足 created_at < '2026-01-01' 和 status='cancelled'。子表删除用 order_id IN (SELECT ...) 或 EXISTS 定位要删的 order_id 集合。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN EXISTS (SELECT 1 FROM order_items i
               WHERE i.order_id NOT IN (SELECT order_id FROM orders))
    THEN 'FAIL: 存在孤儿明细订单已删但明细还在'
  WHEN (SELECT COUNT(*) FROM orders)
       <> (SELECT COUNT(*) FROM base.orders
           WHERE NOT (status='cancelled' AND created_at < '2026-01-01'))
    THEN 'FAIL: 剩余订单数与预期不符（可能删多了或删少了）'
  WHEN (SELECT COUNT(*) FROM order_items)
       <> (SELECT COUNT(*) FROM base.order_items
           WHERE order_id IN (SELECT order_id FROM orders))
    THEN 'FAIL: 明细行数与订单不匹配'
  WHEN EXISTS (SELECT 1 FROM orders o JOIN base.orders b USING(order_id)
               WHERE o.status<>b.status OR o.customer_id<>b.customer_id)
    THEN 'FAIL: 保留了不该被修改的订单数据'
  ELSE 'PASS'
END
""",
        "answer": """
DELETE FROM order_items
WHERE order_id IN (SELECT order_id
                   FROM orders
                   WHERE status = 'cancelled' AND created_at < '2026-01-01');

DELETE FROM orders
WHERE status = 'cancelled' AND created_at < '2026-01-01';
"""},
        "teach": """
删除的正确姿势（**大表尤其重要**）：

1. **顺序**：先子表后主表。外键开启时反着删会报错，这其实是保护机制。
2. **分批**：一次删几十万行会撑爆 undo/回滚段并长时间持锁。 industry做法是
   `DELETE FROM t WHERE 条件 LIMIT 5000;` 循环执行直到 0 行受影响（MySQL），
   SQLite/PG 用 `DELETE FROM t WHERE pk IN (SELECT pk FROM t WHERE 条件 LIMIT 5000)`。
3. **锁**：MySQL InnoDB 的 DELETE 会对扫描到的行加排他锁（next-key lock）。
   扫描范围越大锁越多，阻塞越久 —— 这也是要用索引精确定位的原因。
4. **归档优先**：真正要清理历史数据，应该用 S6-Q06 的思路先搬走到归档表，
   确认无误再删，而不是直接 DELETE。

最容易被忽略的一点：**DELETE 不会立即释放磁盘空间**。
InnoDB 只是标记删除、页可复用；SQLite 同理。真正收缩要 `OPTIMIZE TABLE`（MySQL）
或 `VACUUM`（SQLite/PG）。
""",
    },
    {
        "id": "S6-Q04", "stage": 6, "title": "UPSERT：重复执行不报错", "difficulty": "medium", "points": 12,
        "prompt": """
用**一条** INSERT 完成「有的更新、没有的插入」（幂等写入）：

- product_id=117 的商品，库存改为 1200
- product_id=118 的商品，库存改为 300
- product_id=125 是新品 '测试商品'（分类 5，价格 9.90，库存 50，created_at='2026-09-25 09:00:00'），需要插入

存在冲突时只更新库存即可，其它字段保持不变。这条 SQL 要求能重复跑而不报错。
""",
        "hint": "SQLite 与 PostgreSQL：INSERT ... ON CONFLICT(product_id) DO UPDATE SET stock=excluded.stock。MySQL：INSERT ... ON DUPLICATE KEY UPDATE stock=VALUES(stock)。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN (SELECT COUNT(*) FROM products) <> (SELECT COUNT(*) FROM base.products) + 1
    THEN 'FAIL: 商品总数应为基准+1（新增 1 个、其余被更新）'
  WHEN (SELECT stock FROM products WHERE product_id=117) <> 1200
    THEN 'FAIL: 117 库存应为 1200，实际 ' || COALESCE((SELECT stock FROM products WHERE product_id=117),'不存在')
  WHEN (SELECT stock FROM products WHERE product_id=118) <> 300
    THEN 'FAIL: 118 库存应为 300'
  WHEN NOT EXISTS (SELECT 1 FROM products WHERE product_id=125 AND name='测试商品' AND stock=50)
    THEN 'FAIL: 新商品 125 未插入'
  WHEN EXISTS (SELECT 1 FROM products p JOIN base.products b USING(product_id)
               WHERE p.name<>b.name OR p.price<>b.price OR p.category_id<>b.category_id)
    THEN 'FAIL: 已有商品的其它字段被误改了'
  ELSE 'PASS'
END
""",
        "answer": """
INSERT INTO products(product_id, name, category_id, price, stock, created_at) VALUES
  (117, '纯棉短袖 T 恤', 4, 89.00, 1200, '2025-02-20 09:00:00'),
  (118, '轻薄羽绒服',    4, 599.00, 300,  '2025-11-11 09:00:00'),
  (125, '测试商品',      5, 9.90,   50,   '2026-09-25 09:00:00')
ON CONFLICT(product_id) DO UPDATE SET stock = excluded.stock;
"""},
        "teach": """
UPSERT 解决的是**幂等写入**问题：同一条语句跑 1 次和跑 100 次结果一样。
这是做数据同步、消息消费、对账补偿时的基本要求。

三种方言：

```sql
INSERT INTO t(...) VALUES (...) ON CONFLICT(pk) DO UPDATE SET col=excluded.col;  -- SQLite 3.24+ / PG 9.5+
INSERT INTO t(...) VALUES (...) ON DUPLICATE KEY UPDATE col=VALUES(col);         -- MySQL
MERGE INTO t USING ... WHEN MATCHED THEN UPDATE WHEN NOT MATCHED THEN INSERT;   -- SQL Server / Oracle
```

要点：

- **必须有唯一约束**：冲突检测依赖主键或唯一索引，没有索引的 UPSERT 会退化成纯插入。
- `excluded` 指的是"那个本想插进来却被挡住的行"，别写成一行值都写死的子查询。
- MySQL 的 `VALUES(col)` 在 8.0.20 起被标记为过时，建议改用别名语法
  `INSERT ... VALUES(...) AS new ON DUPLICATE KEY UPDATE col = new.col`。
- 高并发下 UPSERT 依赖唯一索引保证原子性，**不需要**自己先 SELECT 再判断 ——
  那会产生竞态。
""",
    },
    {
        "id": "S6-Q05", "stage": 6, "title": "事务：要么全改，要么一行都不改", "difficulty": "hard", "points": 15,
        "prompt": """
财务部要求：给**技术中心（dept_id = 1）**全员加薪 10%（结果取整）。
但有个硬性前置条件：加薪后该部门**薪资总额不能超过 200000**，超过就必须整体撤销。

请写出一组按顺序执行的 SQL：
1. 先 SELECT 出「加薪后的部门薪资总额」，作为判断依据
2. 若超过阈值，执行 `ROLLBACK`，并向一张名为 `audit_result` 的表写入决策记录
3. 若不超过，`COMMIT` 并同样写入记录
4. `audit_result` 表由你创建，需含 `result` 列（值为 'rolled_back' 或 'committed'），并写入恰好一行
5. 必须显式写 `BEGIN TRANSACTION;`

> 本数据下技术中心加薪后总额会超过阈值，最终数据应当**完全没有变化**。
""",
        "hint": "BEGIN TRANSACTION; -> UPDATE ...; -> 查看总额; -> 因为超阈值，ROLLBACK; -> INSERT INTO audit_result。注意 ROLLBACK 之后刚才 UPDATE 的影响全部消失。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN EXISTS (SELECT 1 FROM employees e JOIN base.employees b USING(emp_id)
               WHERE e.salary <> b.salary)
    THEN 'FAIL: 薪资被部分修改了 —— 这说明 UPDATE 没有被事务包起来，破坏了原子性'
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='audit_result')
    THEN 'FAIL: 没有创建 audit_result 表'
  WHEN (SELECT COUNT(*) FROM audit_result) <> 1
    THEN 'FAIL: audit_result 应恰好一行决策记录'
  WHEN NOT EXISTS (SELECT 1 FROM audit_result WHERE result='rolled_back')
    THEN 'FAIL: 本数据下加薪后总额会超过 200000，决策应当是 rolled_back'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE TABLE audit_result (
    id         INTEGER PRIMARY KEY,
    result     TEXT NOT NULL,
    note       TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

SELECT SUM(CAST(ROUND(salary * 1.1) AS INTEGER)) AS after_total
FROM employees
WHERE dept_id = 1;

BEGIN TRANSACTION;
UPDATE employees
SET salary = CAST(ROUND(salary * 1.1) AS INTEGER)
WHERE dept_id = 1;
ROLLBACK;

INSERT INTO audit_result(id, result, note)
VALUES (1, 'rolled_back', '技术中心加薪后总额超过 200000，整体撤销');
"""},
        "teach": """
事务的意义就是这题的结论：**只要有一条语句失败或主动回滚，之前所有的修改都不作数**。

ACID 里最容易体会错的一条是 Atomicity —— 它不是"每句话单独不出错"，
而是"这组语句对外表现为一个不可分割的整体"。单个 UPDATE 本来就是原子的，
真正的风险来自**多条语句之间的中间状态**被别人读到。

几个必知的细节：

- **DDL 在部分数据库里不能回滚**。MySQL 8.0 之前 `CREATE TABLE` 在事务里会隐式提交；
  PostgreSQL 与 SQLite 的 DDL 是可以回滚的。别跨库套用经验。
- **长事务是性能杀手**。事务期间 undo log 不能清理、锁不能释放，
  从库回放也会堆积延迟。变更类操作要分批 + 短事务。
- **隔离级别**：MySQL InnoDB 默认 RR（可重复读），PostgreSQL 默认 RC（读已提交）。
  同一个"读—判断—写"逻辑在两个库上可能得到不同结果，
  需要保证一致时要显式 `SELECT ... FOR UPDATE` 加行锁，或用 UPSERT/原子更新替代。
""",
    },
    {
        "id": "S6-Q06", "stage": 6, "title": "INSERT ... SELECT 数据归档", "difficulty": "hard", "points": 15,
        "prompt": """
把 **2025 年已完成（completed）** 的订单归档：

1. 创建 `orders_archive` 表，结构与 `orders` 完全相同（含主键与 CHECK 约束）
2. 用 INSERT ... SELECT 把符合条件的订单整行搬过去
3. 从 `orders` 中删除这些被归档的订单
4. 这些订单对应的 `order_items` 明细也要一并删除 —— 否则外键约束会直接拒绝删除订单
   （这正是外键的价值：把错误拦在变更之前，而不是事后修复数据）
5. 要求在 `orders_archive` 上建立 `order_id` 主键（CTAS 简写会丢掉主键，别用它）
""",
        "hint": "CREATE TABLE orders_archive AS SELECT * FROM orders WHERE 1=0 不能复制主键与约束，建议照抄 CREATE TABLE 的完整定义。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders_archive')
    THEN 'FAIL: orders_archive 表不存在'
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders_archive'
                   AND sql LIKE '%PRIMARY KEY%')
    THEN 'FAIL: orders_archive 缺少 PRIMARY KEY'
  WHEN (SELECT COUNT(*) FROM orders_archive)
       <> (SELECT COUNT(*) FROM base.orders
           WHERE status='completed' AND created_at < '2026-01-01')
    THEN 'FAIL: 归档行数与预期不一致'
  WHEN EXISTS (SELECT 1 FROM order_items i
               WHERE i.order_id NOT IN (SELECT order_id FROM orders))
    THEN 'FAIL: 残留孤儿明细（订单已删、明细未删）'
  WHEN EXISTS (SELECT 1 FROM orders o
               WHERE o.order_id IN (SELECT order_id FROM orders_archive))
    THEN 'FAIL: 源表里仍然存在已被归档的订单'
  WHEN EXISTS (SELECT 1 FROM orders_archive a JOIN base.orders b USING(order_id)
               WHERE a.customer_id<>b.customer_id OR a.total_amount<>b.total_amount
                  OR a.created_at<>b.created_at)
    THEN 'FAIL: 归档数据与原始数据不一致'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE TABLE orders_archive (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    status       TEXT    NOT NULL CHECK (status IN ('pending','paid','shipped','completed','cancelled')),
    created_at   TEXT    NOT NULL,
    paid_at      TEXT,
    total_amount NUMERIC NOT NULL DEFAULT 0
);

INSERT INTO orders_archive
SELECT * FROM orders
WHERE status = 'completed' AND created_at < '2026-01-01';

DELETE FROM order_items
WHERE order_id IN (SELECT order_id FROM orders_archive);

DELETE FROM orders
WHERE status = 'completed' AND created_at < '2026-01-01';
"""},
        "teach": """
归档的标准答案是 `INSERT ... SELECT` 而不是先查出内存再逐条 INSERT ——
前者全程在数据库内完成，不产生网络往返，也不占用应用内存。

`CREATE TABLE new AS SELECT ...`（CTAS）这个简写有个**隐蔽缺陷**：

| | CTAS (`CREATE TABLE t AS SELECT`) | 显式 CREATE TABLE + INSERT SELECT |
|---|---|---|
| 列结构 | ✅ 自动 | 手写 |
| 主键/唯一/外键 | ❌ **全部丢失** | ✅ 保留 |
| CHECK 约束 | ❌ 丢失 | ✅ 保留 |
| 索引 | ❌ 丢失 | 需单独建 |
| 默认值 | ❌ 丢失 | ✅ 保留 |

归档表必须显式定义结构。归档表同样需要 `order_id` 主键 —— 否则以后想按单号查历史数据就是全表扫描。

大表归档的正确顺序：`INSERT SELECT`（分批）→ 校验count一致 → 再 `DELETE`（分批）→ 最后 `OPTIMIZE/VACUUM`。
任何一步失败都停在那里，因为数据在归档表里已经有一份了。
""",
    },
]
