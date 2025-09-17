-- 简单迁移脚本：支持同话题多配置功能
-- 如果执行出错，请忽略错误继续执行

-- 删除可能存在的唯一约束（忽略错误）
ALTER TABLE `auto_publish_configs` DROP INDEX `uk_topic_id`;

-- 添加新的复合唯一约束
ALTER TABLE `auto_publish_configs`
ADD UNIQUE KEY `uk_topic_prompt` (`topic_id`, `prompt_key`);

-- 添加索引
ALTER TABLE `auto_publish_configs`
ADD KEY `idx_topic_id` (`topic_id`),
ADD KEY `idx_prompt_key` (`prompt_key`);

-- 为AI对话历史表添加配置ID字段
ALTER TABLE `ai_conversations`
ADD COLUMN `config_id` varchar(50) DEFAULT NULL COMMENT '关联的自动发布配置ID' AFTER `topic_id`;

-- 添加外键约束
ALTER TABLE `ai_conversations`
ADD CONSTRAINT `fk_conversation_config`
FOREIGN KEY (`config_id`) REFERENCES `auto_publish_configs` (`id`)
ON DELETE SET NULL ON UPDATE CASCADE;

-- 添加索引
ALTER TABLE `ai_conversations`
ADD KEY `idx_config_id` (`config_id`),
ADD KEY `idx_topic_config` (`topic_id`, `config_id`);

-- 数据迁移：为现有的对话记录关联配置ID
UPDATE `ai_conversations` ac
INNER JOIN `auto_publish_configs` apc ON ac.topic_id = apc.topic_id
SET ac.config_id = apc.id
WHERE ac.config_id IS NULL;