-- 从 topics 表移除发布方式字段
-- 执行时间: 2024年

-- 移除topics表的publish_type字段
ALTER TABLE `topics` 
DROP COLUMN `publish_type`;

-- 验证字段移除成功
-- SHOW COLUMNS FROM `topics`;