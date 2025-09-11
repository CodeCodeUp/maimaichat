-- 迁移状态跟踪表
-- 用于记录已执行的数据库迁移

CREATE TABLE IF NOT EXISTS `schema_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `version` varchar(50) NOT NULL COMMENT '迁移版本号',
  `name` varchar(200) NOT NULL COMMENT '迁移名称',
  `description` text DEFAULT NULL COMMENT '迁移描述',
  `executed_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
  `execution_time_ms` int(11) DEFAULT NULL COMMENT '执行耗时（毫秒）',
  `checksum` varchar(64) DEFAULT NULL COMMENT '迁移文件校验和',
  `status` enum('success','failed','rollback') NOT NULL DEFAULT 'success' COMMENT '执行状态',
  `error_message` text DEFAULT NULL COMMENT '错误信息',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_version` (`version`),
  KEY `idx_executed_at` (`executed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='迁移状态跟踪表';

-- 插入已完成的迁移记录（如果是从现有系统迁移）
INSERT INTO `schema_migrations` (`version`, `name`, `description`, `executed_at`, `status`) VALUES 
('001', 'add_publish_type_support', '添加发布方式支持（匿名/实名发布）', NOW(), 'success'),
('002', 'add_auto_publish_config_publish_type', '为自动发布配置表添加发布方式字段', NOW(), 'success'),
('003', 'remove_topics_publish_type', '从话题表移除发布方式字段（架构调整）', NOW(), 'success')
ON DUPLICATE KEY UPDATE 
`executed_at` = VALUES(`executed_at`),
`status` = VALUES(`status`);