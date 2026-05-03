USE recharge_db;
-- 给games表加图片URL字段（如果不存在）
ALTER TABLE games ADD COLUMN IF NOT EXISTS icon_url VARCHAR(256) NULL COMMENT '游戏图标图片URL' AFTER icon;
