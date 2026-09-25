# SQL 速查与跨库差异手册

本工作台默认跑 **SQLite 3.53+**（Python 3.13 自带）。下面把「同一件事在三个主流库里怎么写」列成对照表，
把 SQLite 上的本地练习经验迁移到 MySQL / PostgreSQL 时用得上。

> 记不住细节没关系，记住**差异确实存在**这一点，上线前查一遍官方文档即可。

---

## 1. 执行顺序：所有数据库都一样

```
FROM / JOIN     确定数据源
WHERE           逐行过滤
GROUP BY        分组
聚合计算        SUM / COUNT / AVG ...
HAVING          分组后过滤
窗口函数        OVER (...)
SELECT          投影列、计算别名
DISTINCT        整行去重
ORDER BY        排序
LIMIT / OFFSET  截取
```

由此推出的三条硬规则：

1. `WHERE` 里不能用 SELECT 的别名，也不能用聚合函数；
2. `HAVING` 里可以用聚合函数，`WHERE` 里不行；
3. 窗口函数的结果不能在同一层 `WHERE` 里过滤 —— 必须包一层 CTE 或派生表。

---

## 2. 常用语法对照

| 需求 | SQLite | MySQL 8 | PostgreSQL |
|---|---|---|---|
| 截取年月 | `STRFTIME('%Y-%m', d)` | `DATE_FORMAT(d,'%Y-%m')` | `TO_CHAR(d,'YYYY-MM')` |
| 日期加减 | `DATE(d, '+1 month')` | `DATE_ADD(d, INTERVAL 1 MONTH)` | `d + INTERVAL '1 month'` |
| 字符串拼接 | `a || b` | `CONCAT(a,b)` | `a || b` |
| 取 @ 后域名 | `SUBSTR(e, INSTR(e,'@')+1)` | `SUBSTRING_INDEX(e,'@',-1)` | `SPLIT_PART(e,'@',2)` |
| NULL 兜底 | `COALESCE(a,b)` | `COALESCE(a,b)` / `IFNULL(a,b)` | `COALESCE(a,b)` |
| NULL 排最后 | `ORDER BY c NULLS LAST` | `ORDER BY c IS NULL, c`（不支持 NULLS LAST） | `ORDER BY c NULLS LAST` |
| 关联更新 | `UPDATE t SET .. FROM src WHERE ..` | `UPDATE t JOIN src ON .. SET ..` | `UPDATE t SET .. FROM src WHERE ..` |
| UPSERT | `ON CONFLICT(k) DO UPDATE SET c=excluded.c` | `ON DUPLICATE KEY UPDATE c=VALUES(c)` | `ON CONFLICT(k) DO UPDATE SET c=EXCLUDED.c` |
| UPSERT 忽略 | `ON CONFLICT DO NOTHING` | `INSERT IGNORE` | `ON CONFLICT DO NOTHING` |
| 自增主键 | `INTEGER PRIMARY KEY` | `INT AUTO_INCREMENT` | `SERIAL` / `GENERATED ALWAYS AS IDENTITY` |
| 上一行值 | `LAG(x) OVER (...)` | 同（8.0+） | 同 |
| 递归 CTE | `WITH RECURSIVE` | `WITH RECURSIVE`（8.0+） | `WITH RECURSIVE` |
| 复合主键自增 | rowid 隐式 | `AUTO_INCREMENT` 必须为该列建索引 | IDENTITY |
| 布尔类型 | 0/1 | `TINYINT(1)` | `BOOLEAN` |
| 精确小数 | `DECIMAL` 是亲和类型，注意别写成 REAL | `DECIMAL(p,s)` 定点数 | `NUMERIC(p,s)` 任意精度 |

---

## 3. 行为差异（最容易出错的几条）

### NULL 处理

| 场景 | SQLite / PG | MySQL |
|---|---|---|
| NULL 升序位置 | 排最前 | 排最前（一致） |
| `NULLS LAST` 语法 | 支持（SQLite 3.30+） | **不支持**，用 `ORDER BY col IS NULL, col` |
| 唯一索引中的多个 NULL | 允许 | 允许 |
| 字符串拼接遇 NULL | 结果为 NULL | `CONCAT` 遇 NULL 当空串，**与 SQLite 的 `\|\|` 不同！** |

### GROUP BY 严格性

| 库 | SELECT 里出现非分组非聚合列 |
|---|---|
| MySQL 5.7+（ONLY_FULL_GROUP_BY 默认开） | 报错 |
| MySQL 关闭该模式 | **返回一个不确定值** |
| PostgreSQL | 报错 |
| SQLite | 允许，返回该组任意一行 |

→ 结论：**永远写全 GROUP BY**，别指望数据库兜底。

### CHECK 约束

- MySQL **8.0.16 之前只解析不执行** CHECK 约束！跨库移植时这条会静默失效。
- PostgreSQL、SQLite 正常执行。
- CHECK 对 NULL 结果放行 → 必须与 NOT NULL 搭配。

### DDL 与事务

| 库 | 事务中的 DDL |
|---|---|
| MySQL 8.0 之前 | **隐式提交**，不能回滚 |
| MySQL 8.0+ | 支持原子 DDL |
| PostgreSQL | 完全支持回滚 DDL |
| SQLite | 支持回滚 DDL |

### 索引相关术语对照

| 概念 | SQLite 计划输出 | MySQL EXPLAIN | PostgreSQL EXPLAIN |
|---|---|---|---|
| 全表扫描 | `SCAN table` | `type=ALL` | `Seq Scan` |
| 索引查找 | `SEARCH table USING INDEX idx (a=?)` | `type=ref / eq_ref / range` | `Index Scan` |
| 覆盖索引 | `SEARCH table USING COVERING INDEX idx` | `Extra: Using index` | `Index Only Scan` |
| 额外排序 | `USE TEMP B-TREE FOR ORDER BY` | `Extra: Using filesort` | `Sort Key: ...` |
| 临时表 | `USE TEMP B-TREE FOR GROUP BY/DISTINCT` | `Extra: Using temporary` | `HashAggregate / Unique` |

---

## 4. SQLite 特有的坑（本沙箱环境下）

1. **`notnull` 是保留词**：查 pragma 表值函数时要加引号
   ```sql
   SELECT * FROM pragma_table_info('products') WHERE "notnull" = 1;
   ```
2. **`INSERT ... SELECT DISTINCT ... ON CONFLICT DO NOTHING`** 解析会失败，必须带 WHERE：
   ```sql
   INSERT INTO dim(name) SELECT DISTINCT n FROM t WHERE n IS NOT NULL
   ON CONFLICT(name) DO NOTHING;
   ```
3. **外键默认关闭**：每次连接必须 `PRAGMA foreign_keys = ON`（本工作台的 engine 已自动开启）。
4. **行值比较** `(a,b) < (x,y)` 需 SQLite **3.15+**（现已是 3.53，可用）。
5. **没有 `RIGHT/FULL JOIN` 的老版本**：SQLite **3.39+** 才支持（3.53 可用）。
6. 动态类型：声明的类型只是「亲和提示」，`NUMERIC` 列照样能塞字符串 —— 这既是灵活也是风险。

---

## 5. 慢查询排查标准流程

```
1. 拿到慢 SQL          MySQL: slow_query_log / performance_schema
                       PG: pg_stat_statements
                       SQLite: 自己计时 + EXPLAIN QUERY PLAN

2. 看执行计划          先找 type / Extra / rows 三项

3. 定位三大瓶颈        扫描行数是否远超返回行数  → 索引问题
                        Extra 里有 filesort/temporary → 排序/分组问题
                        子查询标记 DEPENDENT       → 改写 JOIN

4. 动手改              加/改索引、改写 SQL、拆批次

5. 复测对比            改前后各跑一次 EXPLAIN + 计时，用数据说话
```

**网络上最常见的三个错误认知**：

- ❌「COUNT(1) 比 COUNT(*) 快」 → 两者在现代优化器里完全等价。
- ❌「索引越多越快」 → 每个索引都是一棵 B-Tree，写放大且干扰优化器选型。
- ❌「加了 LIMIT 就不会慢」 → LIMIT 只减少返回，如果在全表排序中，仍然要扫完全部行。

---

## 6. 安全变更模板（背下来）

```sql
-- 第 1 步：用完全一样的 WHERE 先看影响面
SELECT COUNT(*) FROM orders WHERE status='pending' AND created_at < '2026-08-26';
--   预期 ~N 行。不对就先停在这里搞清楚为什么。

-- 第 2 步：事务里改
BEGIN;
UPDATE orders SET status='cancelled'
WHERE status='pending' AND created_at < '2026-08-26';

-- 第 3 步：改完立刻复核
SELECT COUNT(*) FROM orders WHERE status='pending' AND created_at < '2026-08-26';  -- 应为 0
SELECT status, COUNT(*) FROM orders GROUP BY status;   -- 总量核对

COMMIT;   -- 不对就 ROLLBACK;
```

大表再加两条：**分批**（每批 5000 行以内）和**错峰**（避开业务高峰）。
