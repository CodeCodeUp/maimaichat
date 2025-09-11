-- 迁移脚本: 003_remove_topics_publish_type
-- 创建时间: 2024-09-11
-- 描述: 从话题表移除发布方式字段（架构调整）
-- 影响表: topics
-- 依赖: 002_add_auto_publish_config_publish_type

-- ===============================================
-- 前置检查
-- ===============================================

-- 检查auto_publish_configs表的publish_type字段是否存在
SELECT 'Checking auto_publish_configs.publish_type exists...' as status;

-- ===============================================
-- 执行迁移 - UP
-- ===============================================

-- 移除话题表的发布方式字段索引
ALTER TABLE `topics` DROP KEY IF EXISTS `idx_publish_type`;

-- 移除话题表的发布方式字段
ALTER TABLE `topics` DROP COLUMN IF EXISTS `publish_type`;

-- ===============================================
-- 验证迁移结果
-- ===============================================

-- 验证字段是否移除成功
SELECT 'Verifying migration...' as status;
SHOW COLUMNS FROM `topics` LIKE 'publish_type';

-- 应该返回空结果集，表示字段已被移除
SELECT CASE 
    WHEN (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
          WHERE TABLE_SCHEMA = 'maimaichat' 
          AND TABLE_NAME = 'topics' 
          AND COLUMN_NAME = 'publish_type') = 0 
    THEN 'SUCCESS: publish_type field removed from topics table'
    ELSE 'ERROR: publish_type field still exists in topics table'
END as migration_result;

-- ===============================================
-- 回滚脚本 - DOWN（用于撤销迁移）
-- ===============================================

/*
-- 重新添加发布方式字段到话题表
ALTER TABLE `topics` 
ADD COLUMN `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' 
COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布' 
AFTER `group_name`;

-- 重新添加索引
ALTER TABLE `topics` 
ADD KEY `idx_publish_type` (`publish_type`);
*/