-- 迁移脚本: 允许自动发布配置的topic_id为NULL,支持无话题发布
-- 版本: 003
-- 日期: 2025-01-17

-- 1. 删除原有的外键约束
ALTER TABLE `auto_publish_configs` DROP FOREIGN KEY `fk_auto_publish_topic`;

-- 2. 删除原有的唯一约束
ALTER TABLE `auto_publish_configs` DROP INDEX `uk_topic_id`;

-- 3. 修改topic_id字段为可NULL
ALTER TABLE `auto_publish_configs`
MODIFY COLUMN `topic_id` varchar(50) DEFAULT NULL COMMENT '话题ID(可选,NULL表示无话题发布)';

-- 4. 添加新的组合唯一约束(topic_id + prompt_key),允许NULL值
-- 注意: MySQL的唯一约束中NULL值不参与唯一性检查,所以多个(NULL, 'prompt1')是允许的
ALTER TABLE `auto_publish_configs`
ADD UNIQUE KEY `uk_topic_prompt` (`topic_id`, `prompt_key`);

-- 5. 重新添加外键约束,但允许NULL值
ALTER TABLE `auto_publish_configs`
ADD CONSTRAINT `fk_auto_publish_topic`
FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`)
ON DELETE CASCADE ON UPDATE CASCADE;

-- 说明:
-- 1. 修改后支持创建无话题的自动发布配置
-- 2. 同一话题可以有多个不同提示词的配置
-- 3. 无话题配置可以有多个,通过prompt_key区分
