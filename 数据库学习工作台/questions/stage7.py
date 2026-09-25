# -*- coding: utf-8 -*-
"""阶段 7：建模与约束 —— 主键、NOT NULL、CHECK、外键级联、唯一约束、金额类型、规范化"""

QUESTIONS = [
    {
        "id": "S7-Q01", "stage": 7, "title": "建一张约束齐备的表", "difficulty": "medium", "points": 12,
        "prompt": """
创建商品评价表 `product_reviews`，要求：
- review_id：INTEGER 主键
- product_id：INTEGER NOT NULL，外键指向 products(product_id)，删除商品时级联删除评价
- customer_id：INTEGER NOT NULL，外键指向 customers(customer_id)，**不允许**级联删除
- rating：INTEGER NOT NULL，且必须在 1~5 之间（用 CHECK 约束）
- content：TEXT，可以为空
- created_at：TEXT NOT NULL，默认值为当前时间
- 额外约束：(product_id, customer_id) 唯一，同一个客户对同一商品只能评价一次
""",
        "hint": "SQLite 里 SQLite_VERSION >= 3.6 都支持 CHECK；默认值写 DEFAULT (datetime('now','localtime'))，注意外面要有括号。唯一约束可以写成 CREATE TABLE 里的 UNIQUE(...)，也可以单独建 UNIQUE INDEX。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='product_reviews')
    THEN 'FAIL: product_reviews 表不存在'
  WHEN NOT EXISTS (SELECT 1 FROM pragma_table_info('product_reviews')
                   WHERE name='review_id' AND pk=1 AND UPPER(type)='INTEGER')
    THEN 'FAIL: review_id 必须是 INTEGER 主键'
  WHEN (SELECT COUNT(*) FROM pragma_table_info('product_reviews')
        WHERE name IN ('product_id','customer_id','rating') AND "notnull"=1) <> 3
    THEN 'FAIL: product_id / customer_id / rating 都必须 NOT NULL'
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master
                   WHERE name='product_reviews' AND UPPER(sql) LIKE '%CHECK%RATING%')
    THEN 'FAIL: rating 缺少 CHECK 约束（请把 CHECK 写在 rating 附近）'
  WHEN (SELECT COUNT(*) FROM pragma_foreign_key_list('product_reviews') f
        WHERE f."table" IN ('products','customers')) <> 2
    THEN 'FAIL: 需要两条外键，分别指向 products 和 customers'
  WHEN NOT EXISTS (SELECT 1 FROM pragma_foreign_key_list('product_reviews') f
                   WHERE f."table"='products' AND UPPER(f.on_delete)='CASCADE')
    THEN 'FAIL: 商品外键应带 ON DELETE CASCADE'
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master
                   WHERE UPPER(COALESCE(sql,'')) LIKE '%UNIQUE%'
                     AND (name='product_reviews' OR (type='index' AND LOWER(name) LIKE '%review%')))
    THEN 'FAIL: 未检测到与 product_reviews 相关的唯一约束'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE TABLE product_reviews (
    review_id   INTEGER PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES products(product_id)  ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content     TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE (product_id, customer_id)
);
"""},
        "teach": """
一张表声明约束的成本几乎为零，带来的收益却是长期的：

| 约束 | 拦住的错误 |
|---|---|
| PRIMARY KEY | 重复数据、无法唯一定位一行 |
| NOT NULL | 业务必填字段被漏传 |
| CHECK | 非法枚举值（rating=99、-1） |
| FOREIGN KEY | 孤儿数据、错误的删除顺序 |
| UNIQUE | 业务唯一性被并发破坏 |

几个容易被忽略的细节：

- **CHECK 里的 NULL**：`CHECK (rating BETWEEN 1 AND 5)` 在 rating 为 NULL 时结果是 NULL，
  约束检查会**放行**。所以 CHECK 必须与 NOT NULL 搭配才有意义。
- **外键默认行为是 NO ACTION/RESTRICT**，想级联要显式写 `ON DELETE CASCADE`。
  SQLite 每次连接都要 `PRAGMA foreign_keys=ON` 才生效（MySQL/PG 默认开启）。
- **MySQL 会静默忽略 CHECK**（8.0.16 之前只解析不执行！），跨库移植时别指望它。
- 唯一约束在**除 NULL 外**的值上生效：SQLite/MySQL/PG 的唯一索引都允许多个 NULL 共存，
  这条和"唯一"这个名字有点冲突，需要时把列显式设为 NOT NULL。
""",
    },
    {
        "id": "S7-Q02", "stage": 7, "title": "外键级联删除", "difficulty": "hard", "points": 15,
        "prompt": """
给订单加标签功能：

1. 建表 `order_tags`
   - tag_id INTEGER PRIMARY KEY
   - order_id INTEGER NOT NULL，外键指向 orders(order_id) 且 **ON DELETE CASCADE**
   - tag TEXT NOT NULL
2. 插入 4 行标签：
   - (order_id=10053, tag='加急')、(10053, '需开发票')
   - (order_id=10054, tag='送礼')、(10054, '勿放快递柜')
3. 删除订单 10053：
   - 注意它的明细会阻止直接删除订单（明细外键是 RESTRICT 行为），先删掉它的 `order_items`
   - 再删订单，它的两条标签应该**自动消失**
4. 最终状态：不存在孤儿明细，也不存在孤儿标签
""",
        "hint": "删除顺序：order_items(order_id=10053) -> orders(order_id=10053)，标签由 CASCADE 自动清理。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='order_tags')
    THEN 'FAIL: order_tags 表不存在'
  WHEN NOT EXISTS (SELECT 1 FROM pragma_foreign_key_list('order_tags') f
                   WHERE f."table"='orders' AND UPPER(f.on_delete)='CASCADE')
    THEN 'FAIL: order_id 外键必须声明 ON DELETE CASCADE'
  WHEN EXISTS (SELECT 1 FROM orders WHERE order_id=10053)
    THEN 'FAIL: 订单 10053 没有被删掉'
  WHEN EXISTS (SELECT 1 FROM order_tags WHERE order_id=10053)
    THEN 'FAIL: 订单 10053 的标签没有被级联清理'
  WHEN (SELECT COUNT(*) FROM order_tags WHERE order_id=10054) <> 2
    THEN 'FAIL: 10054 的标签应保留 2 行'
  WHEN EXISTS (SELECT 1 FROM order_items i WHERE i.order_id NOT IN (SELECT order_id FROM orders))
    THEN 'FAIL: 存在孤儿明细'
  WHEN EXISTS (SELECT 1 FROM order_tags t WHERE t.order_id NOT IN (SELECT order_id FROM orders))
    THEN 'FAIL: 存在孤儿标签'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE TABLE order_tags (
    tag_id   INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    tag      TEXT    NOT NULL
);

INSERT INTO order_tags(order_id, tag) VALUES
  (10053, '加急'), (10053, '需开发票'),
  (10054, '送礼'), (10054, '勿放快递柜');

DELETE FROM order_items WHERE order_id = 10053;
DELETE FROM orders     WHERE order_id = 10053;
"""},
        "teach": """
**四种外键删除行为**，选错会直接导致数据不一致：

| 行为 | 删父行时 | 适用场景 |
|---|---|---|
| NO ACTION / RESTRICT | 直接报错拒绝 | 默认值，保护性强。适合"必须有人处理"的关系 |
| CASCADE | 一并删除子行 | 子表是父表的附属物（订单↔订单标签、订单↔明细） |
| SET NULL | 子表外键列置 NULL | 弱关联（员工↔部门解散） |
| SET DEFAULT | 置为默认值 | 很少用 |

关于 CASCADE 的争议：

- **优点**：删了订单，它的标签/明细自动消失，不需要应用层记得补三条 DELETE。
- **风险**：一次 `DELETE FROM orders WHERE created_at < '2025-01-01'` 可能连带删掉几百万行，
  耗时、占锁、撑爆回滚段。生产上大批量删除宁显式分批也不要依赖 CASCADE。

这道题意外的难点在这里：**明细表的外键是 RESTRICT**，
所以你必须先删 `order_items` 才能删订单。这恰恰演示了不同关系选择不同策略的现实：
明细是独立业务事实，不该跟着订单悄悄消失；标签只是附加属性，可以级联。
""",
    },
    {
        "id": "S7-Q03", "stage": 7, "title": "唯一索引与可重入的数据修复", "difficulty": "medium", "points": 12,
        "prompt": """
做一次数据修补，要求**可以重复跑，第二次跑不改变任何东西**：

1. 给 customers.email 建立唯一索引 `ux_customers_email`
2. 把邮箱为空的客户填上默认邮箱：`'user' || customer_id || '@example.com'`（例如 id=13 → user13@example.com）
3. 只更新邮箱为空的行
""",
        "hint": "判断幂等的关键在于 WHERE 条件本身就描述了「目标状态」：email IS NULL 的行才更新，第二次执行时已经没有这样的行了。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master
                   WHERE type='index' AND name='ux_customers_email' AND UPPER(sql) LIKE '%UNIQUE%')
    THEN 'FAIL: 唯一索引 ux_customers_email 不存在'
  WHEN EXISTS (SELECT 1 FROM customers WHERE email IS NULL)
    THEN 'FAIL: 仍有客户邮箱为空'
  WHEN EXISTS (SELECT 1 FROM customers c JOIN base.customers b USING(customer_id)
               WHERE b.email IS NOT NULL AND c.email <> b.email)
    THEN 'FAIL: 误改了原本就有邮箱的客户'
  WHEN (SELECT COUNT(*) FROM customers)
       <> (SELECT COUNT(*) FROM (SELECT DISTINCT email FROM customers))
    THEN 'FAIL: 邮件存在重复值，唯一索引本应拒绝这种情况'
  WHEN NOT EXISTS (SELECT 1 FROM customers WHERE email='user13@example.com')
       AND EXISTS (SELECT 1 FROM base.customers WHERE customer_id=13 AND email IS NULL)
    THEN 'FAIL: 13 号客户的默认邮箱格式不对'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE UNIQUE INDEX ux_customers_email ON customers(email);

UPDATE customers
SET email = 'user' || customer_id || '@example.com'
WHERE email IS NULL;
"""},
        "teach": """
**唯一约束是幂等写入的地基**。有了它，数据库就成了最后的防线：
无论应用层怎么写、并发多少，"同一邮箱只能出现一次"这个规则由引擎担保。

本题的幂等性来自 WHERE 条件的写法 —— 它描述的是**待修复状态**而不是"已执行的次数"。
改成 `UPDATE customers SET email = ...`（没有 WHERE）就会每次把所有邮箱重写一遍，
这种脚本在重 conséquences 真的发生时就是灾难。补数脚本的三条纪律：

1. 更新条件必须等价于"尚未修复"的判定式；
2. 只能走向收敛状态，跑两次与跑一次结果一致；
3. 大表分批 + 记录处理行数，便于中断后续跑。

另外记住：**唯一索引允许多个 NULL 共存**（SQLite/MySQL/PG 都是如此，遵循 SQL 标准），
所以建索引时不会因为有 2 行 email 为 NULL 而失败。如果业务要求"最多一个空邮箱"，
必须先把列改成 NOT NULL，或建部分索引。
""",
    },
    {
        "id": "S7-Q04", "stage": 7, "title": "金额为什么不能用浮点", "difficulty": "hard", "points": 15,
        "prompt": """
结算表和账号流水里用 REAL/FLOAT 存钱是事故高发区。请建立一张**用整数分存储**的结算表：

1. 建表 `settle_bill`
   - bill_id INTEGER PRIMARY KEY
   - order_id INTEGER NOT NULL，外键指向 orders(order_id)
   - customer_id INTEGER NOT NULL
   - amount_cents INTEGER NOT NULL（单位：**分**），并带 CHECK 保证非负
   - settled_at TEXT NOT NULL
2. 把所有 `status='completed'` 的订单搬进去，amount_cents = ROUND(total_amount × 100) 转整数
3. 表中**不允许出现任何浮点类型的列**
""",
        "hint": "CAST(ROUND(total_amount*100) AS INTEGER) 把元转成分。CHECK (amount_cents >= 0)。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='settle_bill')
    THEN 'FAIL: settle_bill 表不存在'
  WHEN NOT EXISTS (SELECT 1 FROM pragma_table_info('settle_bill')
                   WHERE name='amount_cents' AND UPPER(type)='INTEGER')
    THEN 'FAIL: amount_cents 必须是 INTEGER'
  WHEN EXISTS (SELECT 1 FROM pragma_table_info('settle_bill')
               WHERE UPPER(type) IN ('REAL','FLOAT','DOUBLE','NUMERIC'))
    THEN 'FAIL: 出现了浮点类型列，金额必须用整数分存储'
  WHEN (SELECT COUNT(*) FROM settle_bill)
       <> (SELECT COUNT(*) FROM base.orders WHERE status='completed')
    THEN 'FAIL: 结算行数与 completed 订单数不一致'
  WHEN ABS((SELECT SUM(amount_cents) FROM settle_bill) / 100.0
           - (SELECT SUM(ROUND(total_amount*100)) FROM base.orders WHERE status='completed') / 100.0) > 0.01
    THEN 'FAIL: 结算总金额与源数据不一致'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE TABLE settle_bill (
    bill_id      INTEGER PRIMARY KEY,
    order_id     INTEGER NOT NULL REFERENCES orders(order_id),
    customer_id  INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    settled_at   TEXT    NOT NULL
);

INSERT INTO settle_bill(order_id, customer_id, amount_cents, settled_at)
SELECT order_id,
       customer_id,
       CAST(ROUND(total_amount * 100) AS INTEGER),
       created_at
FROM orders
WHERE status = 'completed';
"""},
        "teach": """
**为什么不能用浮点存钱**：0.1 + 0.2 != 0.3。浮点是二进制近似表示，
`(double)19.99 * 100 = 1998.9999999999998`，累加到一定量级就会出现分账对不上，
而且这种错误**不可复现**：同样的 SQL 换个数据规模就换个结果，最难排查。

业界标准做法：

| 方案 | 说明 |
|---|---|
| `DECIMAL(p, s)` | MySQL/PG 的精确小数，最直白。MySQL 里 DECIMAL 是定点数不是浮点 |
| **整数分** | 最通用、跨系统最稳，避免任何精度歧义；缺点是要记得在展示层除以 100 |
| BIGINT + 精度约定 | 加密货币、支付网关常用（如 small = 10^-8 BTC） |

注意 **NUMERIC 不是万能的**：SQLite 的 NUMERIC 只是"亲和类型"，
遇到不能转的值会退化成 REAL；MySQL 的 NUMERIC 等价于 DECIMAL 是安全的，
PostgreSQL 的 NUMERIC 也是任意精度。**跨库时不要假设 NUMERIC 一样。**

展示层的换算也别偷懒：`amount_cents / 100.0` 一旦再参与比较，
同样会引入浮点误差，正确的做法是在最后一步才除、并且立即格式化输出。
""",
    },
    {
        "id": "S7-Q05", "stage": 7, "title": "把反范式宽表规范化为维度表", "difficulty": "hard", "points": 15,
        "prompt": """
`order_flat` 是一张典型的对数仓宽表：客户名、城市、分类名、商品名全被冗余进每一行明细。

请把它规范化 —— 建立客户维度表并回填数据：
1. 建表 `dim_customer`
   - id INTEGER PRIMARY KEY
   - customer_name TEXT NOT NULL **UNIQUE**
   - customer_city TEXT NOT NULL DEFAULT '未知'
2. 用 INSERT ... SELECT 从 order_flat 去重填充，城市为空时存 '未知'
3. 要求这条 INSERT 是**幂等**的（重复执行不报错、不产生重复行）
""",
        "hint": "INSERT ... SELECT DISTINCT ... ON CONFLICT(customer_name) DO NOTHING 可以同时满足去重与幂等。",
        "verify": {"mode": "check", "check": """
SELECT CASE
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='dim_customer')
    THEN 'FAIL: dim_customer 表不存在'
  WHEN NOT EXISTS (SELECT 1 FROM sqlite_master
                   WHERE name='dim_customer' AND UPPER(sql) LIKE '%UNIQUE%')
    THEN 'FAIL: customer_name 缺少唯一约束'
  WHEN (SELECT COUNT(*) FROM dim_customer)
       <> (SELECT COUNT(DISTINCT customer_name) FROM base.order_flat)
    THEN 'FAIL: 维度表行数不等于去重后的客户数'
  WHEN EXISTS (SELECT 1 FROM dim_customer WHERE customer_city IS NULL)
    THEN 'FAIL: 城市不应为 NULL，未知请填"未知"'
  WHEN (SELECT COUNT(*) FROM dim_customer WHERE customer_city='未知')
       <> (SELECT COUNT(DISTINCT customer_name) FROM base.order_flat WHERE customer_city IS NULL)
    THEN 'FAIL: 城市未知的客户统计不正确'
  ELSE 'PASS'
END
""",
        "answer": """
CREATE TABLE dim_customer (
    id            INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL UNIQUE,
    customer_city TEXT NOT NULL DEFAULT '未知'
);

INSERT INTO dim_customer(customer_name, customer_city)
SELECT DISTINCT customer_name,
       COALESCE(customer_city, '未知')
FROM order_flat
WHERE customer_name IS NOT NULL
ON CONFLICT(customer_name) DO NOTHING;
"""},
        "teach": """
规范化解决的是**更新异常**：同一个客户在 order_flat 里重复了 N 次，
他改一次城市就要 UPDATE N 行，漏一行就是脏数据 —— 这叫"修改异常"。

三范式速查：

| 范式 | 要求 | 违反的例子 |
|---|---|---|
| 1NF | 列不可再分、无重复组 | 一个字段里塞 "a,b,c" 逗号分隔 |
| 2NF | 无部分依赖（主键是复合时，非主键列不能只依赖其中一部分） | 明细表里存商品名（只依赖 product_id） |
| 3NF | 无传递依赖 | 明细表里存城市（通过客户传递依赖） |

实操建议：

- **OLTP（业务库）**：默认到 3NF，靠 JOIN 组装视图。`ON CONFLICT DO NOTHING`
  让回填脚本天然幂等 —— 这在 ETL 里是刚需，任务失败重试时不会灌脏数据。
- **OLAP（分析库）**：反而是反范式宽表更快（维度建模里的星型/雪花模型），
  因为省掉 JOIN。同一份数据在不同场景有不同最优结构，这是正常的。

所以 `order_flat` 不是"错误的"，它只是**放在了错的位置**：
业务写入侧应该 3NF，报表查询侧可以物化成宽表。
""",
    },
]
