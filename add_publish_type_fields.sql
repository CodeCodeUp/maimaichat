-- 添加发布方式字段迁移脚本
-- 支持匿名/实名发布功能

-- 1. 为话题表添加发布方式字段
ALTER TABLE `topics` 
ADD COLUMN `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布' 
AFTER `group_name`;

-- 为新字段添加索引
ALTER TABLE `topics` 
ADD KEY `idx_publish_type` (`publish_type`);

-- 2. 为定时发布任务表添加发布方式字段  
ALTER TABLE `scheduled_posts` 
ADD COLUMN `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布'
AFTER `topic_name`;

-- 为新字段添加索引
ALTER TABLE `scheduled_posts` 
ADD KEY `idx_publish_type` (`publish_type`);

-- 3. 检查字段是否添加成功
SHOW COLUMNS FROM `topics` LIKE 'publish_type';
SHOW COLUMNS FROM `scheduled_posts` LIKE 'publish_type';