-- =============================================================
-- 学习沙箱：迷你电商库 (SQLite 3.53+)
-- 8 张表覆盖：字典表 / 主子表 / 一对多 / 自引用树 / 可空列陷阱
-- 所有问答都在这套数据上进行，保证答案可复现。
-- =============================================================

DROP TABLE IF EXISTS order_flat;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

-- 商品分类（字典表，一对多）
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE
);

-- 商品
CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    price       NUMERIC NOT NULL CHECK (price >= 0),   -- 挂牌价
    stock       INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL                       -- 'YYYY-MM-DD HH:MM:SS'
);

-- 客户：city / email 故意留 NULL，专门用来练 IS NULL 语义
CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    city          TEXT,                                -- 可为 NULL
    email         TEXT,                                -- 可为 NULL
    vip_level     INTEGER NOT NULL DEFAULT 0 CHECK (vip_level BETWEEN 0 AND 5),
    registered_at TEXT    NOT NULL
);

-- 订单主表
CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    status       TEXT    NOT NULL CHECK (status IN ('pending','paid','shipped','completed','cancelled')),
    created_at   TEXT    NOT NULL,
    paid_at      TEXT,                                 -- 未支付为 NULL
    total_amount NUMERIC NOT NULL DEFAULT 0
);

-- 订单明细（主子表一对多，复合主键）
CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    item_no    INTEGER NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC NOT NULL,                       -- 成交价，可能与挂牌价不同
    PRIMARY KEY (order_id, item_no)
);

-- 部门
CREATE TABLE departments (
    dept_id INTEGER PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

-- 员工：manager_id 自引用，用于自连接与递归 CTE
CREATE TABLE employees (
    emp_id     INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    dept_id    INTEGER REFERENCES departments(dept_id),
    manager_id INTEGER REFERENCES employees(emp_id),   -- CEO 为 NULL
    salary     INTEGER NOT NULL,
    hired_at   TEXT NOT NULL
);

-- 常用查询加速索引（阶段 8 会要求学员自己分析这些是否够用）
CREATE INDEX idx_orders_customer      ON orders(customer_id);
CREATE INDEX idx_orders_created       ON orders(created_at);
CREATE INDEX idx_order_items_product  ON order_items(product_id);
CREATE INDEX idx_products_category    ON products(category_id);
CREATE INDEX idx_employees_manager    ON employees(manager_id);

-- =============================================================
-- 反范式宽表：客户 / 商品 / 分类信息全部冗余塞进每一行。
-- 阶段 7「规范化」练习的靶子，正常业务查询不要用它。
-- =============================================================
CREATE TABLE order_flat (
    flat_id        INTEGER PRIMARY KEY,
    order_id       INTEGER NOT NULL,
    customer_name  TEXT    NOT NULL,
    customer_city  TEXT,
    category_name  TEXT    NOT NULL,
    product_name   TEXT    NOT NULL,
    quantity       INTEGER NOT NULL,
    unit_price     NUMERIC NOT NULL,
    line_amount    NUMERIC NOT NULL,
    created_at     TEXT    NOT NULL
);
