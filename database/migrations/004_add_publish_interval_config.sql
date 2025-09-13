-- 迁移脚本: 004_add_publish_interval_config
-- 创建时间: 2024-12-30
-- 描述: 为自动发布配置表添加发布间隔配置字段
-- 影响表: auto_publish_configs

-- ===============================================
-- 前置检查
-- ===============================================

-- 检查auto_publish_configs表是否存在
SELECT 'Checking auto_publish_configs table...' as status;

-- ===============================================
-- 执行迁移 - UP
-- ===============================================

-- 为自动发布配置表添加发布间隔配置字段
ALTER TABLE `auto_publish_configs` 
ADD COLUMN `min_interval` int(11) NOT NULL DEFAULT 30 
COMMENT '最小发布间隔（分钟）' 
AFTER `prompt_key`;

ALTER TABLE `auto_publish_configs` 
ADD COLUMN `max_interval` int(11) NOT NULL DEFAULT 60 
COMMENT '最大发布间隔（分钟）' 
AFTER `min_interval`;

-- 为新字段添加索引
ALTER TABLE `auto_publish_configs` 
ADD KEY `idx_interval` (`min_interval`, `max_interval`);

-- ===============================================
-- 数据迁移（如果需要）
-- ===============================================

-- 将现有配置设置为默认值（30-60分钟）
UPDATE `auto_publish_configs` 
SET `min_interval` = 30, `max_interval` = 60 
WHERE `min_interval` IS NULL OR `max_interval` IS NULL;

-- ===============================================
-- 验证迁移结果
-- ===============================================

-- 验证字段是否添加成功
SELECT 'Verifying migration...' as status;
SHOW COLUMNS FROM `auto_publish_configs` LIKE 'min_interval';
SHOW COLUMNS FROM `auto_publish_configs` LIKE 'max_interval';

-- ===============================================
-- 回滚脚本 - DOWN（用于撤销迁移）
-- ===============================================

/*
-- 移除索引
ALTER TABLE `auto_publish_configs` DROP KEY `idx_interval`;

-- 移除字段
ALTER TABLE `auto_publish_configs` DROP COLUMN `min_interval`;
ALTER TABLE `auto_publish_configs` DROP COLUMN `max_interval`;
*/
