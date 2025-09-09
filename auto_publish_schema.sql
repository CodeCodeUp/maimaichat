-- 全自动发布模块表结构

-- 1. 自动发布配置表
CREATE TABLE `auto_publish_configs` (
  `id` varchar(50) NOT NULL COMMENT '配置ID',
  `topic_id` varchar(50) NOT NULL COMMENT '话题ID',
  `max_posts` int(11) NOT NULL DEFAULT -1 COMMENT '最大发布数量，-1表示无限发布',
  `current_posts` int(11) NOT NULL DEFAULT 0 COMMENT '已发布数量',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否激活自动发布',
  `last_published_at` timestamp NULL DEFAULT NULL COMMENT '最后发布时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_topic_id` (`topic_id`),
  KEY `idx_is_active` (`is_active`),
  CONSTRAINT `fk_auto_publish_topic` FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动发布配置表';

-- 2. AI对话历史表
CREATE TABLE `ai_conversations` (
  `id` varchar(50) NOT NULL COMMENT '对话ID',
  `topic_id` varchar(50) NOT NULL COMMENT '话题ID',
  `messages` json NOT NULL COMMENT '对话消息历史',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_topic_id` (`topic_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_conversation_topic` FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话历史表';

-- 3. 扩展定时发布任务表，添加自动发布标识字段
ALTER TABLE `scheduled_posts` 
ADD COLUMN `auto_publish_id` varchar(50) NULL DEFAULT NULL COMMENT '自动发布配置ID' AFTER `topic_name`,
ADD KEY `idx_auto_publish_id` (`auto_publish_id`),
ADD CONSTRAINT `fk_scheduled_post_auto_publish` FOREIGN KEY (`auto_publish_id`) REFERENCES `auto_publish_configs` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;