# -*- coding: utf-8 -*-
"""题库元数据：知识点标签（TAGS）与解题思路（APPROACH）。

为什么要单独放在一个文件里：
- 题面/答案/讲解在一处（stageN.py），元数据在一处（本文件），改题和改分类互不打扰。
- TAGS 是「薄弱点诊断」的统计维度。标签粒度要**恰好是一个可被单独练会的知识点**：
  太粗（比如「JOIN」）定位不出问题，太细（比如「三表 JOIN」）样本太少没有统计意义。
- APPROACH 是「卡住时」的阶梯提示。每一步只给出**下一个动作**，不剧透最终 SQL。
"""

# ---------------------------------------------------------------------------
# 知识点标签 → 用于诊断与重点训练
TAGS = {
    # 阶段 1 查询基础
    "S1-Q01": ["基础过滤", "排序分页"],
    "S1-Q02": ["NULL 语义", "DISTINCT"],
    "S1-Q03": ["聚合函数", "NULL 语义"],
    "S1-Q04": ["字符串函数", "索引失效"],
    "S1-Q05": ["日期处理", "聚合函数"],
    "S1-Q06": ["CASE 表达式", "基础过滤"],
    "S1-Q07": ["字符串函数", "NULL 语义"],
    "S1-Q08": ["排序分页", "NULL 语义"],
    # 阶段 2 聚合与分组
    "S2-Q01": ["LEFT JOIN", "聚合函数", "NULL 语义"],
    "S2-Q02": ["GROUP BY", "聚合函数"],
    "S2-Q03": ["HAVING", "基础过滤", "GROUP BY"],
    "S2-Q04": ["条件聚合", "GROUP BY"],
    "S2-Q05": ["GROUP BY", "LEFT JOIN", "NULL 语义"],
    "S2-Q06": ["派生表", "聚合函数", "GROUP BY"],
    "S2-Q07": ["日期处理", "GROUP BY", "索引失效"],
    # 阶段 3 多表连接
    "S3-Q01": ["JOIN 基础", "排序分页"],
    "S3-Q02": ["LEFT JOIN", "聚合函数", "NULL 语义"],
    "S3-Q03": ["反连接", "NULL 语义"],
    "S3-Q04": ["JOIN 基础", "派生列"],
    "S3-Q05": ["自连接", "LEFT JOIN"],
    "S3-Q06": ["行数膨胀", "派生表", "聚合函数"],
    "S3-Q07": ["JOIN 基础", "派生表", "聚合函数"],
    # 阶段 4 子查询与 CTE
    "S4-Q01": ["标量子查询", "聚合函数"],
    "S4-Q02": ["EXISTS", "去重"],
    "S4-Q03": ["反连接", "NULL 语义"],
    "S4-Q04": ["关联子查询", "聚合函数"],
    "S4-Q05": ["派生表", "GROUP BY", "CASE 表达式"],
    "S4-Q06": ["CTE", "递归CTE", "自连接"],
    "S4-Q07": ["CTE", "递归CTE", "LEFT JOIN", "日期处理"],
    # 阶段 5 窗口函数
    "S5-Q01": ["窗口函数", "CTE", "GROUP BY"],
    "S5-Q02": ["排名函数", "窗口函数", "GROUP BY"],
    "S5-Q03": ["LAG/LEAD", "窗口函数", "CTE"],
    "S5-Q04": ["窗口帧", "窗口函数", "CTE"],
    "S5-Q05": ["窗口帧", "窗口函数", "CTE"],
    "S5-Q06": ["排名函数", "窗口函数", "CTE", "去重"],
    "S5-Q07": ["窗口函数", "GROUP BY", "聚合函数"],
    # 阶段 6 变更与事务
    "S6-Q01": ["INSERT", "外键"],
    "S6-Q02": ["UPDATE", "派生表"],
    "S6-Q03": ["DELETE", "外键", "主子表顺序"],
    "S6-Q04": ["UPSERT", "唯一约束"],
    "S6-Q05": ["事务", "UPDATE", "原子性"],
    "S6-Q06": ["数据归档", "INSERT SELECT", "DELETE"],
    # 阶段 7 建模与约束
    "S7-Q01": ["表设计", "约束", "外键"],
    "S7-Q02": ["外键", "约束", "主子表顺序"],
    "S7-Q03": ["唯一约束", "UPDATE", "幂等"],
    "S7-Q04": ["数据类型", "表设计", "约束"],
    "S7-Q05": ["规范化", "表设计", "UPSERT"],
    # 阶段 8 索引与执行计划
    "S8-Q01": ["单列索引", "执行计划"],
    "S8-Q02": ["联合索引", "执行计划"],
    "S8-Q03": ["覆盖索引", "执行计划"],
    "S8-Q04": ["索引失效", "日期处理", "执行计划"],
    "S8-Q05": ["排序优化", "联合索引", "执行计划"],
    "S8-Q06": ["冗余索引", "联合索引"],
    # 阶段 9 调优实战
    "S9-Q01": ["深分页", "排序优化"],
    "S9-Q02": ["COUNT 优化", "覆盖索引", "执行计划"],
    "S9-Q03": ["查询改写", "GROUP BY", "关联子查询"],
    "S9-Q04": ["TOP-N", "排序优化", "执行计划"],
    # 阶段 10 综合融合作战（标签刻意跨阶段，用来检验「能不能把知识串起来」）
    "S10-Q01": ["聚合函数", "NULL 语义", "条件聚合"],
    "S10-Q02": ["LEFT JOIN", "GROUP BY", "条件聚合", "去重"],
    "S10-Q03": ["反连接", "标量子查询", "窗口函数", "CTE"],
    "S10-Q04": ["CTE", "排名函数", "窗口函数", "CASE 表达式"],
    "S10-Q05": ["数据归档", "INSERT SELECT", "主子表顺序", "表设计"],
    "S10-Q06": ["联合索引", "排序优化", "覆盖索引", "执行计划"],
}

# ---------------------------------------------------------------------------
# 解题思路：每一步只说「下一个该干什么」，不剧透最终 SQL。
# 前端会逐条解锁；最后一步通常是「验证」而不是「写出答案」。
APPROACH = {
    "S1-Q01": [
        "先确定数据源只有一张 orders 表，不需要 JOIN。",
        "把筛选条件 status = 'completed' 放进 WHERE —— 过滤要在排序之前发生。",
        "ORDER BY total_amount DESC 决定顺序，LIMIT 10 放最后；子句顺序写错就是语法错误。",
        "跑完看一眼行数是不是 10，再抽查最大金额是不是全表最大的那笔。",
    ],
    "S1-Q02": [
        "去重用 DISTINCT，但要先想清楚「对谁去重」——这里只对 city 一列。",
        "NULL 不是值，不能用 = 或 <> 判断，必须用 IS NULL / IS NOT NULL。",
        "WHERE 先剔除 NULL，再 DISTINCT，最后 ORDER BY。",
        "验证：结果行数应等于城市种类数，且不含 NULL。",
    ],
    "S1-Q03": [
        "三个指标都来自同一张表，用「一条 SELECT + 三个聚合」而不是三次查询。",
        "COUNT(*) 数所有行，COUNT(email) 数 email 非 NULL 的行。",
        "两者相减就是 email 为空的行数。",
        "验证：has_email_cnt + no_email_cnt 应等于 total_cnt。",
    ],
    "S1-Q04": [
        "模糊匹配用 LIKE，通配符 % 表示任意长度。",
        "中文子串匹配要写成 '%机%'，两边都有通配符。",
        "排序放在最后。",
        "顺手想一下：前后都带 % 时，B-Tree 索引能不能定位起点？",
    ],
    "S1-Q05": [
        "日期是文本，按字典序比较即可，直接用 > 和 <。",
        "把「上半年」翻译成半开区间：>= '2026-01-01' AND < '2026-07-01'。",
        "聚合用 COUNT(*) 与 SUM，金额用 ROUND 保留两位。",
        "验证：把条件改成下半年再跑一次，两次金额相加应接近全站金额。",
    ],
    "S1-Q06": [
        "分级用 CASE WHEN，分支从最严到最宽写，利用短路特性。",
        "外层 WHERE 先限定只看 3000 以上的订单，减少参与计算的行。",
        "别忘了 ELSE 分支，否则漏掉的会返回 NULL。",
        "验证：三个等级的行数相加应等于过滤后的总行数。",
    ],
    "S1-Q07": [
        "city 为 NULL 时用 COALESCE 换成可读文本。",
        "email 为 NULL 要单独用 CASE 判断，再决定取域名还是占位符。",
        "取 @ 之后的部分：SUBSTR(email, INSTR(email,'@') + 1)。",
        "验证：检查那 2 位无邮箱客户的 email_domain 是不是 '-'。",
    ],
    "S1-Q08": [
        "先按 vip_level 降序，这是主排序键。",
        "城市未知的要排最后：SQLite 用 NULLS LAST，其他库用 ORDER BY city IS NULL, city。",
        "最后加一个确定性排序键（registered_at），保证同一条 SQL 两次执行结果一致。",
        "验证：结果里 NULL 城市是不是都落在末尾。",
    ],

    "S2-Q01": [
        "要保留从没下单的客户，就必须 LEFT JOIN，而且要写在 FROM 侧。",
        "聚合时数的是右表的非空列 COUNT(o.order_id)，写 COUNT(*) 会把 0 单客户记成 1。",
        "COUNT(o.paid_at) 天然实现了「只数已支付的」，比 CASE WHEN 更短。",
        "验证：应有 5 位客户 order_cnt = 0。",
    ],
    "S2-Q02": [
        "按 status 分组，一个 GROUP BY 里可以放多个聚合函数。",
        "聚合函数会忽略 NULL；AVG 的分母只数非空行。",
        "金额统一 ROUND 到两位。",
        "验证：五个 status 的 order_cnt 相加应等于 280。",
    ],
    "S2-Q03": [
        "先分清两种过滤：过滤原始行 → WHERE；过滤分组结果 → HAVING。",
        "排除取消订单是对单行判断，放 WHERE（更早生效，扫得更少）。",
        "订单数 >= 5 是对分组的判断，只能在 HAVING。",
        "验证：随便挑一个结果里的客户，手工数一下他的有效订单数。",
    ],
    "S2-Q04": [
        "长表转宽表用条件聚合：SUM(CASE WHEN 条件 THEN 1 ELSE 0 END)。",
        "五个状态写五个 CASE，共用同一个 GROUP BY。",
        "必须 LEFT JOIN 才能保留 0 单客户；ELSE 0 保证他们得到 0 而不是 NULL。",
        "验证：任一客户五个状态计数之和，应等于他的总订单数。",
    ],
    "S2-Q05": [
        "要保留全部 24 个商品，从 products 出发做 LEFT JOIN。",
        "GROUP BY 要写全所有非聚合列（product_id + name）。",
        "SUM 在全 NULL 组会返回 NULL，用 COALESCE 兜底成 0。",
        "验证：结果应有 24 行，且有 3 行 sold_qty = 0。",
    ],
    "S2-Q06": [
        "两层聚合：内层先算出「每个客户几单」，外层再统计「多少客户属于哪一类」。",
        "内层用 LEFT JOIN + COUNT(右表列) 才能包含 0 单客户。",
        "算比率时写 100.0 * x / y，否则整数除法会先截断。",
        "验证：ordered_customers + 未下单客户数 应等于 40。",
    ],
    "S2-Q07": [
        "用 STRFTIME('%Y-%m', created_at) 把时间戳压成月份。",
        "GROUP BY 后面重复同一个表达式（或用别名，SQLite/MySQL 允许）。",
        "排序按 ym 升序。",
        "顺手判断一下：在列上套函数之后，created_at 的索引还能不能用？",
    ],

    "S3-Q01": [
        "写一列 JOIN ... ON（连接条件）而不是逗号式连接（容易漏条件产生笛卡尔积）。",
        "连接条件放 ON，业务过滤留 WHERE，职责分开。",
        "给两张表各起一个短别名，所有列都带前缀。",
        "验证：结果行数应与 orders 相同，因为每笔订单都有客户。",
    ],
    "S3-Q02": [
        "滞销品也要出现 → products 作左表，LEFT JOIN order_items。",
        "计数用 COUNT(i.order_id)（右表非空列），不是 COUNT(*)。",
        "SUM 结果套 COALESCE(..., 0)。",
        "验证：应有 24 行，且胶片机套装/羊毛针织帽/有机山茶油的销量为 0。",
    ],
    "S3-Q03": [
        "「没有对应记录」的查询叫反连接。安全写法：LEFT JOIN + 右表主键 IS NULL。",
        "判断 NULL 只能用 IS NULL，千万不要写 o.order_id = NULL。",
        "也可以用 NOT EXISTS，语义更贴近「存在与否」。",
        "验证：结果应有 5 行；试着改成 NOT IN 看看有没有差别。",
    ],
    "S3-Q04": [
        "从明细表出发，沿外键血缘向上连：item → orders → products → categories。",
        "每条 JOIN 都对应一个明确的外键。",
        "line_amount 这类派生金额现场算，不要落库。",
        "验证：抽查一行，quantity × unit_price 是否等于 line_amount。",
    ],
    "S3-Q05": [
        "自连接就是同一张表起两个别名：e 本人、m 上级。",
        "顶层人员 manager_id 是 NULL，所以必须用 LEFT JOIN，否则 CEO 会消失。",
        "上级名用 COALESCE 兜底成 '—'。",
        "验证：结果应有 15 行，且正好 5 行 manager 为 '—'。",
    ],
    "S3-Q06": [
        "先想清楚粒度：orders 是一单一行，order_items 是一明细一行，直接 JOIN 会让主表行被复制。",
        "所以先把明细按 order_id 聚合压成一单一行，再 JOIN。",
        "然后才能放心 SUM(o.total_amount)。",
        "验证：把两种写法的结果都跑一遍，看放大版是不是明显偏大。",
    ],
    "S3-Q07": [
        "逗号式连接漏条件 = 笛卡尔积，先确认自己每条 JOIN 都有 ON。",
        "客户数、商品数用 COUNT(DISTINCT ...)，它们在明细粒度上重复出现。",
        "金额不在明细粒度上，用标量子查询单独求和，避免被放大。",
        "验证：line_cnt 应等于 order_items 表的总行数。",
    ],

    "S4-Q01": [
        "阈值是「全站平均」，用标量子查询算出来，它返回一行一列可以当值用。",
        "把子查询放在 WHERE 的比较右侧；也可以放进 SELECT 列表当展示列。",
        "子查询必须恰好返回一行一列 —— 多行会直接报错。",
        "验证：结果里所有 total_amount 都应大于 avg_amount。",
    ],
    "S4-Q02": [
        "「至少买过一件」是存在性判断，用 EXISTS 最贴切。",
        "EXISTS 找到第一条就短路，天然去重，不需要 DISTINCT。",
        "子查询里必须写 i.order_id = o.order_id 与外层关联，否则退化成恒真。",
        "验证：结果里不应出现同一个 order_id 两次。",
    ],
    "S4-Q03": [
        "反连接优先用 NOT EXISTS（安全）或 LEFT JOIN ... IS NULL。",
        "NOT IN 遇到子查询含 NULL 时会返回空集 —— 记住这条，别用它。",
        "按 product_id 排序。",
        "验证：应有 3 行，就是那三个滞销品。",
    ],
    "S4-Q04": [
        "「每个客户的最新一单」= 对每个客户各算一次 MAX(created_at)，用关联子查询。",
        "子查询里写 o2.customer_id = c.customer_id 与外层关联。",
        "外层用 created_at = 子查询 定位那一行。",
        "验证：结果行数应等于有订单的客户数（35）。",
    ],
    "S4-Q05": [
        "分两层：内层派生表先按客户汇总出金额，外层再分层统计。",
        "分层 CASE 要写在外层 GROUP BY 的同一层。",
        "GROUP BY 后面可以直接用 SELECT 的别名（SQLite/MySQL 支持）。",
        "验证：三档的 cust_cnt 相加应等于有订单的客户数。",
    ],
    "S4-Q06": [
        "递归 CTE = 锚成员（顶层，manager_id IS NULL）+ UNION ALL + 递归成员（引用自身）。",
        "必须用 UNION ALL 而不是 UNION（UNION 会去重）。",
        "递归成员里 JOIN org，并且要逐步收敛。",
        "验证：应有 15 行，level 最大为 3。",
    ],
    "S4-Q07": [
        "补零的关键是「维度序列做左表」——序列必须完整，聚合结果可能缺行。",
        "用 WITH RECURSIVE 生成 ym：起点 '2026-01'，DATE(ym||'-01','+1 month') 推进。",
        "LEFT JOIN 月度聚合结果，缺失的用 COALESCE 补 0。",
        "验证：必须返回 9 行，即使某个月完全没有订单。",
    ],

    "S5-Q01": [
        "窗口函数在 GROUP BY 之后才计算，所以「先聚合再开窗」必须分两层 CTE。",
        "第一层算出每个商品的销售额，第二层按分类分区排名。",
        "PARTITION BY 分类，ORDER BY 金额 DESC，取 rn <= 2。",
        "验证：每个分类最多 2 行。",
    ],
    "S5-Q02": [
        "同一个 OVER (ORDER BY ...) 上叠三个排名函数，直接对比行为差异。",
        "ROW_NUMBER 加第二排序键保证确定性；RANK 并列跳号；DENSE_RANK 并列不跳号。",
        "排名结果不能在同一层 WHERE 过滤，但这里只需要展示。",
        "验证：找一组并列销量的商品，看 rk 是否相同而 rn 不同。",
    ],
    "S5-Q03": [
        "先用一个 CTE 算出每月 GMV，再在它之上做窗口计算。",
        "LAG(gmv) OVER (ORDER BY ym) 取上个月的值。",
        "除零要用 NULLIF 防御，首月自然为 NULL。",
        "验证：首月 mom_pct 应为 NULL，其余月份有值。",
    ],
    "S5-Q04": [
        "先 CTE 算月度 GMV。",
        "累计用 SUM(gmv) OVER (ORDER BY ym ROWS UNBOUNDED PRECEDING ... AND CURRENT ROW)。",
        "ROWS 是按物理行数，RANGE 是按值域 —— 这里用 ROWS。",
        "验证：最后一行的 running_total 应等于全站 GMV。",
    ],
    "S5-Q05": [
        "移动平均只需把窗口帧改成 ROWS BETWEEN 2 PRECEDING AND CURRENT ROW。",
        "前几个月行数不足时，SQLite 会按实际行数平均。",
        "同样先 CTE 算月度值。",
        "验证：第 3 行的 ma3 应等于前三个月 gmv 的平均。",
    ],
    "S5-Q06": [
        "「每组取一条」用 ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) 最稳。",
        "务必加第二排序键（order_id DESC），否则并列时结果不确定。",
        "窗口函数不能在同一层 WHERE 过滤 → 必须包一层 CTE，外层 WHERE rn = 1。",
        "验证：每个客户有且只有一行，共 35 行。",
    ],
    "S5-Q07": [
        "分组聚合与窗口聚合可以叠在一起：内层 SUM 是分组，外层 SUM() OVER () 是全窗口。",
        "OVER () 没有 PARTITION/ORDER，窗口就是整个结果集，每行拿到同一个总计。",
        "记得写 100.0，整数除法会截断。",
        "验证：所有 pct 相加应约等于 100。",
    ],

    "S6-Q01": [
        "先看外键方向：orders.customer_id 引用 customers，所以先插客户再插订单。",
        "customer_id 让数据库生成，子表引用时用标量子查询反查，不要猜自增 ID。",
        "分号分隔的两条 INSERT 按顺序执行。",
        "验证：SELECT COUNT(*) 分别确认客户数和订单数各 +1。",
    ],
    "S6-Q02": [
        "想把「一批行」的值刷进另一批行，用 UPDATE ... FROM（MySQL 是 UPDATE ... JOIN）。",
        "FROM 侧放一个按 order_id 聚合好的派生表，保证一单一行。",
        "WHERE 里写连接条件，把派生表对上目标表。",
        "验证：改完后抽查几笔订单的手工计算结果是否一致。",
    ],
    "S6-Q03": [
        "删除顺序是「先子后主」——明细外键会阻止你直接删订单。",
        "先 DELETE order_items（用 IN 或 EXISTS 定位要删的 order_id）。",
        "再 DELETE orders，条件要同时限定状态和时间。",
        "验证：确认没有孤儿明细，且非目标的订单一行没少。",
    ],
    "S6-Q04": [
        "「有的更新、没有的插入」用 UPSERT：ON CONFLICT(product_id) DO UPDATE。",
        "冲突检测依赖主键/唯一约束，products 的主键是 product_id。",
        "excluded.stock 指的是那个「本想插进来却被挡住」的行。",
        "验证：把整条 SQL 再跑一遍，结果应完全不变（幂等）。",
    ],
    "S6-Q05": [
        "先 SELECT 出加薪后的部门总额，作为判断依据。",
        "用 BEGIN TRANSACTION 把 UPDATE 包起来；判断超阈值就 ROLLBACK，否则 COMMIT。",
        "记录决策的表要在事务之外创建和写入，否则会被一起回滚。",
        "验证：ROLLBACK 后所有薪资应与原始值完全一致。",
    ],
    "S6-Q06": [
        "归档表必须显式 CREATE TABLE（含主键），CTAS 简写会丢掉主键、索引、约束。",
        "用 INSERT INTO ... SELECT 一次性搬数据，全程在数据库内完成。",
        "删数据前先删子表明细，外键会挡住你。",
        "验证：归档行数应与源数据筛选结果一致，且源表已无重复行。",
    ],

    "S7-Q01": [
        "逐列想清楚约束：主键、NOT NULL、CHECK、外键、唯一。",
        "CHECK 对 NULL 会放行，所以 rating 必须同时 NOT NULL。",
        "级联写 ON DELETE CASCADE，默认的 RESTRICT 不会联动。",
        "验证：试着插一条 rating = 9 的数据，应该被 CHECK 拒绝。",
    ],
    "S7-Q02": [
        "外键删除行为要显式声明 ON DELETE CASCADE，默认是不联动。",
        "先删明细（RESTRICT 挡着你），再删订单，标签由 CASCADE 自动清掉。",
        "插入标签时确认 order_id 真实存在。",
        "验证：删完订单后，查 order_tags 里不应再有它的记录。",
    ],
    "S7-Q03": [
        "幂等的关键是 WHERE 描述「尚未修复的状态」，而不是「执行次数」。",
        "先建唯一索引，它天然允许多个 NULL 共存。",
        "UPDATE 只改 email IS NULL 的行，第二次跑时已无符合条件者。",
        "验证：整组语句连跑两次，结果应完全相同。",
    ],
    "S7-Q04": [
        "金额不用浮点：用整数存「分」，元转分是 ROUND(x*100) 后 CAST 成 INTEGER。",
        "表定义里 CHECK (amount_cents >= 0) 兜底。",
        "INSERT ... SELECT 从 orders 直接搬，别在应用层循环。",
        "验证：归档总金额除以 100 应与源表金额一致。",
    ],
    "S7-Q05": [
        "先建维表：主键 + 业务唯一键（customer_name UNIQUE）。",
        "回填用 INSERT ... SELECT DISTINCT，从宽表抽取去重后的客户。",
        "加 ON CONFLICT DO NOTHING 让回填天然幂等。",
        "验证：维表行数应等于宽表里去重后的客户数。",
    ],

    "S8-Q01": [
        "先用 EXPLAIN QUERY PLAN 看当前是不是 SCAN orders（全表扫）。",
        "建立单列索引 idx_orders_status。",
        "再看计划：应变成 SEARCH orders USING INDEX ...",
        "验证：断言里不应再出现 SCAN orders。",
    ],
    "S8-Q02": [
        "联合索引的列顺序决定能不能用上：等值列在前、范围列在后。",
        "查询里必须带上最左列 customer_id，索引才能定位。",
        "带上了 created_at 的范围条件，计划里应出现两个列都被用上。",
        "验证：只查 created_at 的写法会不会用到这个索引？自己试一次。",
    ],
    "S8-Q03": [
        "回表 = 拿着索引里的主键再查一次主键树，是随机 IO。",
        "把要用的列（price）也放进索引，就变成覆盖索引。",
        "看计划里有没有 COVERING INDEX 字样。",
        "验证：对比建索引前后的计划文本差异。",
    ],
    "S8-Q04": [
        "函数包在列上，索引存的原始值就无法二分定位 → 计划变成 SCAN。",
        "把「年份 = 2026」翻译成「created_at >= '2026-01-01' AND < '2027-01-01'」。",
        "列是裸的，索引可以做范围定位。",
        "验证：计划应出现 SEARCH 与 created_at>? / created_at<?。",
    ],
    "S8-Q05": [
        "ORDER BY 想免排序，索引列顺序必须与排序列同序同向。",
        "建 (customer_id, created_at)，再按 (customer_id, created_at) 排序。",
        "看计划里 USE TEMP B-TREE FOR ORDER BY 是否消失。",
        "验证：改成一个方向混合的排序（一个 ASC 一个 DESC），看排序是否回来。",
    ],
    "S8-Q06": [
        "已有 (a, b) 之后，单独的 (a) 就是冗余 —— 它正是联合索引的最左前缀。",
        "但单独的 (b) 不是冗余，按时间统计仍然需要。",
        "先建联合索引，再 DROP 冗余的那个。",
        "验证：用 sqlite_master 确认最终索引清单符合预期。",
    ],

    "S9-Q01": [
        "OFFSET 要先生成再丢弃前 N 行，越翻越慢；游标分页直接定位起点。",
        "排序键必须唯一，所以用 (created_at, order_id) 复合键。",
        "用行值比较 (created_at, order_id) < (游标值) 一次写清。",
        "验证：与 OFFSET 版的结果对比，前 10 行应完全一致。",
    ],
    "S9-Q02": [
        "COUNT(*) 不需要读具体列，只要确定行数。",
        "把 WHERE 写成半开区间，让它落在 created_at 索引上。",
        "看计划是否出现 SEARCH ... USING COVERING INDEX。",
        "验证：结果行数应等于 2026 年的订单数。",
    ],
    "S9-Q03": [
        "相关子查询会外层每行执行一次，改写成 JOIN + GROUP BY 一次扫完。",
        "时间范围和状态放 WHERE，分组后 HAVING 做金额阈值。",
        "注意 HAVING 里可以写聚合条件，WHERE 里不行。",
        "验证：抽查一个结果客户，手工核对他的 2026 年有效订单金额。",
    ],
    "S9-Q04": [
        "TOP-N 的正确做法是让索引替你排序，而不是全表排序再截断。",
        "建 idx_orders_amount，索引叶子天然有序。",
        "看计划里 USE TEMP B-TREE FOR ORDER BY 是否消失。",
        "验证：结果应是金额最大的 5 笔订单。",
    ],

    "S10-Q01": [
        "所有指标都来自同一张表，用「一条 SELECT + 多个聚合表达式」而不是多次查询。",
        "统计缺失值：COUNT(col) 会跳过 NULL，所以缺失数 = COUNT(*) - COUNT(col)。",
        "带条件的计数写成 SUM(CASE WHEN ... THEN 1 ELSE 0 END)，记得 ELSE。",
        "验证：vip3_cnt 应等于单独跑一遍 SELECT COUNT(*) WHERE vip_level>=3 的结果。",
    ],
    "S10-Q02": [
        "城市未知要归到一组并显示为 '未知'，所以分组键要写 COALESCE(c.city, '未知')，不能写 c.city。",
        "JOIN 之后一个客户会出现 N 行，数人数必须用 COUNT(DISTINCT ...)。",
        "「下过单的客户数」用 COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN c.customer_id END)。",
        "验证：每个城市的 ordered_cnt + never_ordered_cnt 应等于 customer_cnt。",
    ],
    "S10-Q03": [
        "第一层 CTE：categories JOIN products 保证分类齐全，再 LEFT JOIN order_items 才不会漏滞销品。",
        "动销计数用 COUNT(DISTINCT CASE WHEN i.order_id IS NOT NULL THEN p.product_id END)。",
        "第二层用 SUM(amount) OVER () 拿总销售额算占比，比子查询干净。",
        "最高价商品用关联标量子查询，ORDER BY 务必加第二排序键 product_id 保证确定性。",
    ],
    "S10-Q04": [
        "分三层：第一层 GROUP BY 聚合成「一人一行」，第二层开窗算排名与占比，第三层才做 CASE 分层。",
        "同一层里不能既算窗口函数又引用它的别名，所以分层必须放在外层。",
        "排名用 RANK 而不是 ROW_NUMBER —— 金额并列就该并列，否则分层边界会漂。",
        "验证：rk<=5 的行 tier 应全为 '头部'，且 pct 之和接近 100。",
    ],
    "S10-Q05": [
        "顺序不能变：先 CREATE TABLE（显式写主键），再 INSERT SELECT 备份，最后才删。",
        "删数据必须先删子表 order_items，外键 RESTRICT 会挡住你直接删订单。",
        "DELETE 用 IN (SELECT order_id FROM 归档表) 定位，避免条件写两遍不一致。",
        "收尾必须输出核对报告：归档行数、源表剩余、孤儿明细数（应为 0）。",
    ],
    "S10-Q06": [
        "等值列在前、排序列在后，所以索引是 (customer_id, created_at)。",
        "ORDER BY 是 DESC，索引里也要显式写 created_at DESC，否则引擎仍要多排一次序。",
        "只 SELECT 需要的四列，有机会变成覆盖索引连回表都省掉。",
        "验证：计划里应出现这个索引名，且没有 USE TEMP B-TREE FOR ORDER BY。",
    ],
}

# ---------------------------------------------------------------------------
# 标签 → 所属阶段，用于给出「回哪个阶段补」的建议
TAG_STAGE = {
    "基础过滤": 1, "NULL 语义": 1, "字符串函数": 1, "日期处理": 1, "CASE 表达式": 1,
    "DISTINCT": 1, "排序分页": 1, "去重": 1, "派生列": 1,
    "聚合函数": 2, "GROUP BY": 2, "HAVING": 2, "条件聚合": 2, "派生表": 2,
    "JOIN 基础": 3, "LEFT JOIN": 3, "反连接": 3, "自连接": 3, "行数膨胀": 3,
    "标量子查询": 4, "EXISTS": 4, "关联子查询": 4, "CTE": 4, "递归CTE": 4,
    "窗口函数": 5, "排名函数": 5, "LAG/LEAD": 5, "窗口帧": 5,
    "INSERT": 6, "UPDATE": 6, "DELETE": 6, "UPSERT": 6, "事务": 6,
    "数据归档": 6, "INSERT SELECT": 6, "主子表顺序": 6, "原子性": 6, "幂等": 6,
    "表设计": 7, "约束": 7, "外键": 7, "唯一约束": 7, "数据类型": 7, "规范化": 7,
    "执行计划": 8, "单列索引": 8, "联合索引": 8, "覆盖索引": 8, "索引失效": 8,
    "排序优化": 8, "冗余索引": 8,
    "深分页": 9, "COUNT 优化": 9, "查询改写": 9, "TOP-N": 9,
}


def tags_for(qid: str) -> list:
    return TAGS.get(qid, [])


def approach_for(qid: str) -> list:
    return APPROACH.get(qid, [])
