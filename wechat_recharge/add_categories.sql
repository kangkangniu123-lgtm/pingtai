-- 在原有数据库基础上新增，执行方式：mysql -u root -p recharge_db < add_categories.sql

USE recharge_db;

-- 游戏分类表
CREATE TABLE IF NOT EXISTS categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(32) NOT NULL COMMENT '分类名称，如：热门游戏',
    icon        VARCHAR(8)  NOT NULL DEFAULT '🎮' COMMENT 'emoji图标',
    sort_order  INT DEFAULT 0,
    is_active   TINYINT(1) DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 游戏表
CREATE TABLE IF NOT EXISTS games (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL COMMENT '所属分类',
    name        VARCHAR(64) NOT NULL COMMENT '游戏名称',
    icon        VARCHAR(8)  DEFAULT '🎮' COMMENT 'emoji图标',
    cover_color VARCHAR(16) DEFAULT '#1a1a2e' COMMENT '封面渐变色',
    description VARCHAR(128) COMMENT '简介',
    sort_order  INT DEFAULT 0,
    is_active   TINYINT(1) DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- products表新增game_id字段（关联游戏表）
ALTER TABLE products ADD COLUMN game_id INT NULL AFTER game_name;
ALTER TABLE products ADD INDEX idx_game_id (game_id);

-- 插入示例分类
INSERT INTO categories (name, icon, sort_order) VALUES
('新游首发', '🆕', 1),
('热门游戏', '🔥', 2),
('特价专区', '💰', 3),
('主机游戏', '🕹️', 4);

-- 插入示例游戏
INSERT INTO games (category_id, name, icon, cover_color, description, sort_order) VALUES
(2, '原神', '✨', '#1a3a5c', '开放世界冒险RPG', 1),
(2, '王者荣耀', '⚔️', '#1a2a1a', '5v5竞技手游', 2),
(2, '和平精英', '🎯', '#2a1a0a', '大逃杀射击手游', 3),
(1, '鸣潮', '🌊', '#0a1a2a', '开放世界动作RPG', 4),
(3, '崩坏：星穹铁道', '🚂', '#1a0a2a', '回合制策略RPG', 5),
(4, 'PS Store', '🎮', '#00439c', 'PlayStation充值', 6);

-- 把原有products关联到游戏
UPDATE products SET game_id = (SELECT id FROM games WHERE name = products.game_name LIMIT 1);
