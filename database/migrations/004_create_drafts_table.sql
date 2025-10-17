-- 创建草稿箱表
-- 迁移编号: 004
-- 说明: 添加草稿箱功能，支持保存、编辑和批量发布草稿

-- 12. 草稿箱表
CREATE TABLE IF NOT EXISTS `drafts` (
  `id` varchar(50) NOT NULL COMMENT '草稿ID',
  `title` varchar(500) NOT NULL DEFAULT '' COMMENT '标题',
  `content` text NOT NULL COMMENT '内容',
  `topic_url` varchar(500) DEFAULT NULL COMMENT '话题URL',
  `topic_id` varchar(50) DEFAULT NULL COMMENT '话题ID',
  `circle_type` varchar(20) DEFAULT NULL COMMENT '圈子类型',
  `topic_name` varchar(200) DEFAULT NULL COMMENT '话题名称',
  `publish_type` enum('anonymous','real_name') NOT NULL DEFAULT 'anonymous' COMMENT '发布方式: anonymous=匿名发布, real_name=实名发布',
  `source` varchar(50) DEFAULT 'manual' COMMENT '来源: manual=手动创建, parsed=JSON解析',
  `tags` varchar(500) DEFAULT NULL COMMENT '标签，逗号分隔',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_topic_id` (`topic_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_source` (`source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='草稿箱表';
