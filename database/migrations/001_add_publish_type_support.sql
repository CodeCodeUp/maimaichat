-- 迁移脚本: 001_add_publish_type_support
-- 创建时间: 2024-09-11
-- 描述: 添加发布方式支持（匿名/实名发布）
-- 影响表: topics, scheduled_posts

-- ===============================================
-- 前置检查
-- ===============================================

-- 检查表是否存在
SELECT 'Checking tables existence...' as status;

-- ===============================================
-- 执行迁移 - UP
-- ===============================================

-- 1. 为话题表添加发布方式字段
ALTER TABLE `topics` 
ADD COLUMN `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' 
COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布' 
AFTER `group_name`;

-- 为新字段添加索引
ALTER TABLE `topics` 
ADD KEY `idx_publish_type` (`publish_type`);

-- 2. 为定时发布任务表添加发布方式字段  
ALTER TABLE `scheduled_posts` 
ADD COLUMN `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' 
COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布'
AFTER `topic_name`;

-- 为新字段添加索引
ALTER TABLE `scheduled_posts` 
ADD KEY `idx_publish_type` (`publish_type`);

-- ===============================================
-- 数据迁移（如果需要）
-- ===============================================

-- 默认所有现有记录为匿名发布
-- UPDATE `topics` SET `publish_type` = 'anonymous' WHERE `publish_type` IS NULL;
-- UPDATE `scheduled_posts` SET `publish_type` = 'anonymous' WHERE `publish_type` IS NULL;

-- ===============================================
-- 验证迁移结果
-- ===============================================

-- 验证字段是否添加成功
SELECT 'Verifying migration...' as status;
SHOW COLUMNS FROM `topics` LIKE 'publish_type';
SHOW COLUMNS FROM `scheduled_posts` LIKE 'publish_type';

-- ===============================================
-- 回滚脚本 - DOWN（用于撤销迁移）
-- ===============================================

/*
-- 移除索引
ALTER TABLE `topics` DROP KEY `idx_publish_type`;
ALTER TABLE `scheduled_posts` DROP KEY `idx_publish_type`;

-- 移除字段
ALTER TABLE `topics` DROP COLUMN `publish_type`;
ALTER TABLE `scheduled_posts` DROP COLUMN `publish_type`;
*/