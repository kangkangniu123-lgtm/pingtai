-- database.sql
-- 运行方式: mysql -u root -p < database.sql

CREATE DATABASE IF NOT EXISTS recharge_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recharge_db;

-- 创建专用数据库用户
CREATE USER IF NOT EXISTS 'recharge_user'@'localhost' IDENTIFIED BY 'niuniu123';
GRANT ALL PRIVILEGES ON recharge_db.* TO 'recharge_user'@'localhost';
FLUSH PRIVILEGES;

-- 用户表（微信用户）
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    openid      VARCHAR(64) NOT NULL UNIQUE COMMENT '微信openid',
    nickname    VARCHAR(64) COMMENT '微信昵称',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_openid (openid)
) ENGINE=InnoDB;

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    game_name   VARCHAR(64) NOT NULL COMMENT '游戏名称',
    name        VARCHAR(128) NOT NULL COMMENT '商品名称，如：100钻石',
    price       DECIMAL(10,2) NOT NULL COMMENT '售价（元）',
    cost        DECIMAL(10,2) COMMENT '成本价（元）',
    description VARCHAR(256) COMMENT '商品描述',
    is_active   TINYINT(1) DEFAULT 1 COMMENT '是否上架',
    sort_order  INT DEFAULT 0 COMMENT '排序',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_game (game_name),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    order_no        VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号',
    openid          VARCHAR(64) NOT NULL COMMENT '用户openid',
    product_id      INT NOT NULL COMMENT '商品ID',
    product_name    VARCHAR(128) NOT NULL COMMENT '商品名称快照',
    game_name       VARCHAR(64) NOT NULL COMMENT '游戏名称快照',
    amount          DECIMAL(10,2) NOT NULL COMMENT '支付金额',
    game_account    VARCHAR(128) NOT NULL COMMENT '游戏账号',
    game_zone       VARCHAR(64) COMMENT '游戏区服',
    game_role       VARCHAR(64) COMMENT '游戏角色名',
    remark          VARCHAR(256) COMMENT '用户备注',
    pay_status      TINYINT(1) DEFAULT 0 COMMENT '支付状态: 0待支付 1已支付',
    order_status    TINYINT(1) DEFAULT 0 COMMENT '订单状态: 0待处理 1处理中 2已完成 3已退款',
    wx_transaction_id VARCHAR(64) COMMENT '微信支付流水号',
    paid_at         DATETIME COMMENT '支付时间',
    completed_at    DATETIME COMMENT '完成时间',
    admin_remark    VARCHAR(256) COMMENT '管理员备注',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_openid (openid),
    INDEX idx_order_no (order_no),
    INDEX idx_status (pay_status, order_status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- access_token缓存表
CREATE TABLE IF NOT EXISTS wx_token_cache (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    token       VARCHAR(512) NOT NULL,
    expires_at  DATETIME NOT NULL
) ENGINE=InnoDB;

-- 插入示例商品数据
INSERT INTO products (game_name, name, price, cost, description, sort_order) VALUES
('原神', '创世神晶×60', 6.00, 5.00, '充值后请提供UID，将直接发送至邮箱', 1),
('原神', '创世神晶×300+30', 30.00, 25.00, '充值后请提供UID，将直接发送至邮箱', 2),
('原神', '创世神晶×980+110', 98.00, 85.00, '充值后请提供UID，将直接发送至邮箱', 3),
('王者荣耀', '点券×648', 6.00, 5.20, '请提供游戏账号和区服', 10),
('王者荣耀', '点券×3288', 30.00, 26.00, '请提供游戏账号和区服', 11),
('和平精英', '未知碎片×60', 6.00, 5.00, '请提供游戏UID', 20);
