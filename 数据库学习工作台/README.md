# 数据库学习工作台

一套**能真跑、能自动判分**的 SQL 学习环境。零第三方依赖，只用 Python 标准库（`sqlite3` + `http.server`）。

- **63 道题**，覆盖 10 个阶段，共 751 分（含 6 道跨阶段融合题）
- **8 张表**的迷你电商沙箱（含外键、自引用树、刻意留的 NULL、滞销商品、反范式宽表）
- **三种判分模式**：结果集比对、自定义校验、执行计划断言
- **两种练习界面**：浏览器工作台 + 命令行闯关
- **完整学习闭环**：间隔复习、错题本、薄弱点诊断、标记笔、分层解题思路

---

## 快速开始

```bash
# 1. 重建沙箱数据库（生成 sandbox/learn.db）
python run.py init

# 2. 启动浏览器工作台（自动打开 http://127.0.0.1:8787）
python run.py web

# 也可以用命令行：
python run.py list --stage 3          # 看某阶段的题
python run.py show S5-Q01             # 看题面（含提示，不含答案）
python run.py check S5-Q01 -f a.sql   # 用文件里的 SQL 提交判分
python run.py exam --stage 3 -n 5     # 交互式做 5 道题
python run.py step  S5-Q01            # 逐条看解题思路（不剧透答案）
python run.py reveal S5-Q01           # 看参考答案 + 知识点讲解

# 学习闭环
python run.py review --do             # 今日复习队列（也可 --do 直接开做）
python run.py wrong  --do             # 错题集 / 重做未攻克的题
python run.py diagnose                # 薄弱点诊断 + 重点训练建议
python run.py note   S5-Q01           # 写笔记 + 打标记（⭐收藏/❗易错/✓已掌握）
python run.py notes -o notes.md       # 导出全部笔记、标记与划重点
python run.py progress                # 学习进度
python run.py selftest                # 题库自检（参考答案是否仍有效）
```

---

## 目录结构

```
数据库学习工作台/
├── run.py                    命令行总入口
├── README.md                 本文件
├── sandbox/
│   ├── schema.sql            表结构（8 张表 + 索引 + 约束）
│   ├── seed.py               确定性种子数据（固定随机种子 → 答案可复现）
│   └── learn.db              生成的数据库（题库的唯一基准）
├── questions/
│   ├── stage1.py             阶段 1：查询基础
│   ├── ...
│   ├── stage9.py             阶段 9：调优实战
│   ├── stage10.py            阶段 10：综合融合作战（6 道融合题）
│   └── meta.py               知识点标签 + 解题思路（诊断与分层提示的数据源）
├── engine/
│   ├── db.py                 SQL 拆分执行、结果归一化、库副本管理
│   ├── grader.py             判分引擎（exact / check / plan）
│   ├── loader.py             题库加载与元数据合并
│   ├── progress.py           进度、错题、笔记、标记、划重点
│   └── review.py             间隔复习排期、融合题解锁、薄弱点诊断
├── web/
│   ├── server.py             本地 HTTP 服务（标准库）
│   └── static/index.html     单页练习界面
├── syllabus/
│   ├── 学习路线图.md          阶段目标、知识点、自测清单
│   └── SQL速查与跨库差异.md   SQLite / MySQL / PostgreSQL 对照
└── progress/progress.json     做题记录（可版本管理）
```

---

## 判分机制

每道题在 `questions/stageN.py` 里是一个字典，`verify` 决定怎么判：

**1. exact —— 结果集比对**

```python
{"mode": "exact", "answer": "SELECT ..."}
```
把标准答案和你的 SQL 各跑一遍，比较「排序后的行多重集」。
- 不受返回顺序影响
- 数值有容差：`|a-b| <= max(0.005, |a|*1e-9)`，所以 `ROUND(SUM(x),2)` 与裸 `SUM(x)` 都能通过
- `check_columns: True` 时同时校验列名

**2. check —— 自定义校验 SQL**（DML/DDL 题目用这个）

```python
{"mode": "check", "check": "SELECT CASE WHEN ... THEN 'PASS' ELSE 'FAIL: ...' END"}
```
先执行你的 SQL，再执行校验 SQL，取第一行第一列：
- 字符串以 `PASS` 开头（或为 `OK`/`TRUE`）→ 通过
- 数值等于 1 → 通过
- 其余当作失败原因返回

**关键能力**：校验 SQL 里可以访问两个库 ——
`main.*` 是你改过之后的数据，`base.*` 是**未被污染的原始基准库**。
所以能做逐行比对级别的精确判定。

**3. plan —— 执行计划断言**（阶段 8/9 用这个）

```python
{"mode": "plan",
 "contains": ["SEARCH orders USING INDEX idx_orders_status"],
 "not_contains": ["SCAN orders"]}
```
对你的最后一条 SELECT 跑 `EXPLAIN QUERY PLAN`，做子串断言（忽略大小写）。

---

## 隔离设计

| 操作 | 用的库 | 说明 |
|---|---|---|
| 自由练习（「运行」按钮） | `sandbox/sessions/<会话>.db` | 每个浏览器一份独立副本，随便改 |
| 提交判分 | 临时目录里的全新副本 | 重复提交同一条 SQL 结果永远一致 |
| 题库基准 | `sandbox/learn.db` | 永远只读，不会被污染 |

「重置数据」按钮把会话副本恢复成基准状态。

---

## 沙箱数据

| 表 | 行数 | 说明 |
|---|---|---|
| categories | 5 | 商品分类字典表 |
| products | 24 | 商品（含 3 个零销量滞销品、2 个零库存） |
| customers | 40 | 客户（3 位城市未知、2 位无邮箱、5 位从未下单） |
| orders | 280 | 订单主表（5 种状态，paid_at 可空） |
| order_items | 564 | 明细（复合主键） |
| departments | 5 | 部门 |
| employees | 15 | 员工（`manager_id` 自引用，5 个根节点） |
| order_flat | 564 | 反范式宽表（阶段 7 规范化的靶子） |

数据由固定随机种子生成，**任何人、任何时间重建都完全一致**，因此题目答案可复现。

---

## 学习闭环是怎么运转的

```
做题 → 答错自动进错题本 → 答对排入间隔复习（1/2/4/7/15/30/60 天）
                                    ↓
            诊断：按知识点标签算掌握度 → 指出薄弱块 + 推荐练哪几题
                                    ↓
       阶段全部通关 → 解锁对应融合题（必须综合前 N 阶段才能做出来）
```

| 能力 | 怎么用 |
|---|---|
| 间隔复习 | 答对拉长间隔，答错退回 1 天后重做；手动打「❗」会立刻进队列 |
| 错题本 | 每次答错自动入册（含错误原因与当时的 SQL），重做通过后标记「已攻克」移出 |
| 薄弱诊断 | 按 `TAGS` 统计掌握度，输出「先补哪块、重点练哪几题」 |
| 标记笔 | 题面里选中一段文字 → 浮出「✎ 标记这段」→ 写批注，之后以黄色高亮显示 |
| 重做 / 重置 | `python run.py reset ...` | 见下节「重置：想重做一遍怎么办」 |
| 分层思路 | 「💡 看思路」一次只展开一步，最后一步教你怎么验证，不直接给答案 |

## 重置：想重做一遍怎么办

```bash
python run.py reset --question S3-Q03   # 重做这一题
python run.py reset --stage 3           # 重置整个阶段
python run.py reset --all               # 清空全部记录（自动备份到 progress.backup.json）
python run.py reset --all --hard        # 连笔记、标记一起清
```

默认**只清答题记录**（次数 / 通过 / 错题 / 复习排期），**保留笔记、标记、划重点** ——
重做的目的是重练，不是把笔记弄丢。要连笔记一起清才加 `--hard`。

网页端三个入口，注意别混：

| 按钮 | 作用 |
|---|---|
| 编辑器栏「↺ 重做」 | 清空当前这道题的答题记录 |
| 顶栏「重置进度」 | 抽屉里可选单题 / 阶段 / 全部，可勾选是否清笔记 |
| 顶栏「重置练习库」 | **只还原数据库**（把改乱的表恢复初始），不动学习记录 |

## 加一道自己的题

在 `questions/stageN.py` 里追加一个字典：

```python
{
    "id": "S3-Q08", "stage": 3, "title": "...", "difficulty": "medium", "points": 8,
    "prompt": "题面，支持 Markdown（代码块、表格、加粗）",
    "hint": "想不出来时看的提示",
    "verify": {"mode": "exact", "answer": "SELECT ..."},
    "teach": "知识点讲解，支持 Markdown",
}
```

然后跑 `python run.py selftest` 自检 —— 它会把所有参考答案重新判一遍，
确保不会因为数据变动或语法差异导致「答对了也判错」。

---

## 常见问题

**Q：能不能换成 MySQL / PostgreSQL？**
本工作台的执行与判分依赖 SQLite。若要迁移：`schema.sql` 需改写类型与自增语法，
`seed.py` 保持不变即可，`questions/` 里的答案要按 `syllabus/SQL速查与跨库差异.md` 的对照表重写。

**Q：为什么有些题我写对了却判错？**
先看「对比/反馈」标签页。最常见三类：
1. 多表查询列名没有加表别名前缀 → 报 `ambiguous column name`
2. 返回值排序不同（判分已忽略顺序，所以这种情况不会误判）
3. 少了 ORDER BY 第二排序键导致的并列行

**Q：把练习库改乱了怎么办？**
不用担心：你改的是会话副本，判分永远在全新副本上跑。真乱了就点「重置数据」。
