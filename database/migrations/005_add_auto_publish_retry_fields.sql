-- 迁移脚本: 005_add_auto_publish_retry_fields
-- 创建时间: 2024-12-30
-- 描述: 为自动发布配置表添加失败重试相关字段
-- 影响表: auto_publish_configs

-- ===============================================
-- 前置检查
-- ===============================================

-- 检查auto_publish_configs表是否存在
SELECT 'Checking auto_publish_configs table...' as status;

-- ===============================================
-- 执行迁移 - UP
-- ===============================================

-- 为自动发布配置表添加失败重试相关字段
ALTER TABLE `auto_publish_configs` 
ADD COLUMN `retry_count` int(11) NOT NULL DEFAULT 0 
COMMENT '当前重试次数' 
AFTER `max_interval`;

ALTER TABLE `auto_publish_configs` 
ADD COLUMN `max_retry` int(11) NOT NULL DEFAULT 3 
COMMENT '最大重试次数' 
AFTER `retry_count`;

ALTER TABLE `auto_publish_configs` 
ADD COLUMN `last_error` text DEFAULT NULL 
COMMENT '最后一次错误信息' 
AFTER `max_retry`;

-- ===============================================
-- 数据迁移（如果需要）
-- ===============================================

-- 将现有配置的重试次数设置为0，最大重试次数设置为3
UPDATE `auto_publish_configs` 
SET `retry_count` = 0, `max_retry` = 3 
WHERE `retry_count` IS NULL OR `max_retry` IS NULL;

-- ===============================================
-- 验证迁移结果
-- ===============================================

-- 验证字段是否添加成功
SELECT 'Verifying migration...' as status;
SHOW COLUMNS FROM `auto_publish_configs` LIKE 'retry_count';
SHOW COLUMNS FROM `auto_publish_configs` LIKE 'max_retry';
SHOW COLUMNS FROM `auto_publish_configs` LIKE 'last_error';

-- ===============================================
-- 回滚脚本 - DOWN（用于撤销迁移）
-- ===============================================

/*
-- 移除字段
ALTER TABLE `auto_publish_configs` DROP COLUMN `retry_count`;
ALTER TABLE `auto_publish_configs` DROP COLUMN `max_retry`;
ALTER TABLE `auto_publish_configs` DROP COLUMN `last_error`;
*/