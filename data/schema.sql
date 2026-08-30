-- ============================================================
-- data/schema.sql
-- E-Commerce analytics database schema
-- Run: mysql -u root -p < data/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecommerce_db;
USE ecommerce_db;

-- ── Customers ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id   INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    phone         VARCHAR(20),
    city          VARCHAR(60),
    state         VARCHAR(40),
    region        VARCHAR(30),          -- North / South / East / West
    segment       VARCHAR(30),          -- Consumer / Corporate / SME
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Products ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id    INT AUTO_INCREMENT PRIMARY KEY,
    product_name  VARCHAR(150) NOT NULL,
    category      VARCHAR(60)  NOT NULL,
    sub_category  VARCHAR(60),
    unit_price    DECIMAL(10,2) NOT NULL,
    cost_price    DECIMAL(10,2) NOT NULL,
    stock_qty     INT DEFAULT 0
);

-- ── Sales Representatives ───────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_reps (
    rep_id        INT AUTO_INCREMENT PRIMARY KEY,
    rep_name      VARCHAR(100) NOT NULL,
    region        VARCHAR(30),
    target_amount DECIMAL(12,2) DEFAULT 0
);

-- ── Orders ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id      INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT          NOT NULL,
    rep_id        INT,
    order_date    DATE         NOT NULL,
    ship_date     DATE,
    status        VARCHAR(30)  DEFAULT 'Completed',  -- Completed / Returned / Pending
    payment_mode  VARCHAR(30),                        -- Online / COD / Card
    INDEX idx_customer (customer_id),
    INDEX idx_date     (order_date),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (rep_id)      REFERENCES sales_reps(rep_id)
);

-- ── Order Items ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    item_id       INT AUTO_INCREMENT PRIMARY KEY,
    order_id      INT           NOT NULL,
    product_id    INT           NOT NULL,
    quantity      INT           NOT NULL DEFAULT 1,
    unit_price    DECIMAL(10,2) NOT NULL,
    discount_pct  DECIMAL(5,2)  DEFAULT 0.00,
    INDEX idx_order   (order_id),
    INDEX idx_product (product_id),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ── Useful view: order revenue summary ─────────────────────
CREATE OR REPLACE VIEW vw_order_revenue AS
SELECT
    o.order_id,
    o.customer_id,
    CONCAT(c.first_name,' ',c.last_name) AS customer_name,
    c.segment,
    c.region,
    o.order_date,
    o.status,
    o.rep_id,
    sr.rep_name,
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct/100)) AS revenue,
    SUM(oi.quantity * (oi.unit_price - p.cost_price) * (1 - oi.discount_pct/100)) AS profit
FROM orders o
JOIN customers    c  ON o.customer_id = c.customer_id
JOIN order_items  oi ON o.order_id    = oi.order_id
JOIN products     p  ON oi.product_id = p.product_id
LEFT JOIN sales_reps sr ON o.rep_id  = sr.rep_id
GROUP BY o.order_id, o.customer_id, customer_name, c.segment,
         c.region, o.order_date, o.status, o.rep_id, sr.rep_name;
