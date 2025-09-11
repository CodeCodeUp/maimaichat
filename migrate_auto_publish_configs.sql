-- 为 auto_publish_configs 表添加发布方式字段
-- 执行时间: 2024年

-- 添加发布方式字段到自动发布配置表
ALTER TABLE `auto_publish_configs` 
ADD COLUMN `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' 
COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布' 
AFTER `topic_id`;

-- 验证字段添加成功
-- SHOW COLUMNS FROM `auto_publish_configs` LIKE 'publish_type';