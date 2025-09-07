-- 脉脉自动发布系统数据库表结构
-- 数据库: maimaichat

-- 1. AI配置表
CREATE TABLE `ai_configs` (
  `id` varchar(50) NOT NULL COMMENT '配置ID',
  `name` varchar(100) NOT NULL COMMENT '配置名称',
  `description` text COMMENT '描述',
  `api_key` varchar(200) NOT NULL COMMENT 'API密钥',
  `base_url` varchar(200) NOT NULL COMMENT 'API基础URL',
  `main_model` varchar(100) NOT NULL COMMENT '主要模型',
  `assistant_model` varchar(100) DEFAULT '' COMMENT '助手模型',
  `enabled` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI配置表';

-- 2. AI配置设置表
CREATE TABLE `ai_config_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(50) NOT NULL COMMENT '设置键',
  `setting_value` varchar(200) NOT NULL COMMENT '设置值',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_setting_key` (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI配置设置表';

-- 3. 定时HTTP请求表
CREATE TABLE `scheduled_requests` (
  `id` varchar(50) NOT NULL COMMENT '请求ID',
  `name` varchar(200) NOT NULL COMMENT '请求名称',
  `url` text NOT NULL COMMENT '请求URL',
  `method` varchar(10) NOT NULL DEFAULT 'GET' COMMENT 'HTTP方法',
  `headers` json DEFAULT NULL COMMENT '请求头',
  `cookies` json DEFAULT NULL COMMENT 'Cookie信息',
  `data` json DEFAULT NULL COMMENT '请求数据',
  `enabled` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `last_executed` timestamp NULL DEFAULT NULL COMMENT '最后执行时间',
  `last_result` json DEFAULT NULL COMMENT '最后执行结果',
  `execution_count` int(11) DEFAULT 0 COMMENT '执行次数',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_enabled` (`enabled`),
  KEY `idx_last_executed` (`last_executed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时HTTP请求表';

-- 4. 定时发布任务表
CREATE TABLE `scheduled_posts` (
  `id` varchar(50) NOT NULL COMMENT '任务ID',
  `title` varchar(500) NOT NULL COMMENT '标题',
  `content` text NOT NULL COMMENT '内容',
  `topic_url` varchar(500) DEFAULT NULL COMMENT '话题URL',
  `topic_id` varchar(50) DEFAULT NULL COMMENT '话题ID',
  `circle_type` varchar(20) DEFAULT NULL COMMENT '圈子类型',
  `topic_name` varchar(200) DEFAULT NULL COMMENT '话题名称',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending, published, failed',
  `scheduled_at` timestamp NOT NULL COMMENT '计划发布时间',
  `published_at` timestamp NULL DEFAULT NULL COMMENT '实际发布时间',
  `error` text DEFAULT NULL COMMENT '错误信息',
  `failed_at` timestamp NULL DEFAULT NULL COMMENT '失败时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`),
  KEY `idx_scheduled_at` (`scheduled_at`),
  KEY `idx_topic_id` (`topic_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时发布任务表';

-- 5. 话题表
CREATE TABLE `topics` (
  `id` varchar(50) NOT NULL COMMENT '话题ID',
  `name` varchar(500) NOT NULL COMMENT '话题名称',
  `circle_type` varchar(20) DEFAULT NULL COMMENT '圈子类型',
  `group_name` varchar(100) DEFAULT NULL COMMENT '分组名称',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_group_name` (`group_name`),
  KEY `idx_circle_type` (`circle_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='话题表';

-- 6. 提示词表
CREATE TABLE `prompts` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `name` varchar(100) NOT NULL COMMENT '提示词名称',
  `content` text NOT NULL COMMENT '提示词内容',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提示词表';

-- 7. 关键词分组表
CREATE TABLE `keyword_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `group_name` varchar(100) NOT NULL COMMENT '分组名称',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_group_name` (`group_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键词分组表';

-- 8. 关键词表
CREATE TABLE `keywords` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `group_name` varchar(100) NOT NULL COMMENT '分组名称',
  `keyword` varchar(200) NOT NULL COMMENT '关键词',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_group_name` (`group_name`),
  UNIQUE KEY `uk_group_keyword` (`group_name`, `keyword`),
  CONSTRAINT `fk_keywords_group` FOREIGN KEY (`group_name`) REFERENCES `keyword_groups` (`group_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键词表';

-- 插入AI配置设置的默认值
INSERT INTO `ai_config_settings` (`setting_key`, `setting_value`) VALUES ('current_config_id', '');