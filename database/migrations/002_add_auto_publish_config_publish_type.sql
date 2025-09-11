-- 迁移脚本: 002_add_auto_publish_config_publish_type
-- 创建时间: 2024-09-11
-- 描述: 为自动发布配置表添加发布方式字段
-- 影响表: auto_publish_configs

-- ===============================================
-- 前置检查
-- ===============================================

-- 检查auto_publish_configs表是否存在
SELECT 'Checking auto_publish_configs table...' as status;

-- ===============================================
-- 执行迁移 - UP
-- ===============================================

-- 为自动发布配置表添加发布方式字段
ALTER TABLE `auto_publish_configs` 
ADD COLUMN `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' 
COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布' 
AFTER `topic_id`;

-- 为新字段添加索引
ALTER TABLE `auto_publish_configs` 
ADD KEY `idx_publish_type` (`publish_type`);

-- 为自动发布配置表添加提示词字段（如果还没有）
ALTER TABLE `auto_publish_configs` 
ADD COLUMN `prompt_key` varchar(100) DEFAULT NULL 
COMMENT '使用的提示词键名' 
AFTER `publish_type`;

-- ===============================================
-- 数据迁移（如果需要）
-- ===============================================

-- 默认所有现有配置为匿名发布
-- UPDATE `auto_publish_configs` SET `publish_type` = 'anonymous' WHERE `publish_type` IS NULL;

-- ===============================================
-- 验证迁移结果
-- ===============================================

-- 验证字段是否添加成功
SELECT 'Verifying migration...' as status;
SHOW COLUMNS FROM `auto_publish_configs` LIKE 'publish_type';
SHOW COLUMNS FROM `auto_publish_configs` LIKE 'prompt_key';

-- ===============================================
-- 回滚脚本 - DOWN（用于撤销迁移）
-- ===============================================

/*
-- 移除索引
ALTER TABLE `auto_publish_configs` DROP KEY `idx_publish_type`;

-- 移除字段
ALTER TABLE `auto_publish_configs` DROP COLUMN `publish_type`;
ALTER TABLE `auto_publish_configs` DROP COLUMN `prompt_key`;
*/