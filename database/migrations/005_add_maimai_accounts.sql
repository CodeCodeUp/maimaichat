-- 多账号支持迁移
-- 迁移编号: 005
-- 说明: 添加脉脉账号管理表,支持配置多个access_token,并为相关表添加account_id字段

-- 1. 创建脉脉账号表
CREATE TABLE IF NOT EXISTS `maimai_accounts` (
  `id` varchar(50) NOT NULL COMMENT '账号ID',
  `name` varchar(200) NOT NULL COMMENT '账号名称(用于识别)',
  `access_token` varchar(500) NOT NULL COMMENT '访问令牌',
  `description` text COMMENT '账号描述',
  `is_default` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否默认账号(1=是,0=否)',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用(1=启用,0=禁用)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_is_default` (`is_default`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='脉脉账号表';

-- 2. 为定时发布表添加账号ID字段
ALTER TABLE `scheduled_posts`
ADD COLUMN `account_id` varchar(50) DEFAULT NULL COMMENT '关联的脉脉账号ID' AFTER `publish_type`,
ADD KEY `idx_account_id` (`account_id`);

-- 3. 为草稿箱表添加账号ID字段
ALTER TABLE `drafts`
ADD COLUMN `account_id` varchar(50) DEFAULT NULL COMMENT '关联的脉脉账号ID' AFTER `publish_type`,
ADD KEY `idx_account_id` (`account_id`);

-- 4. 为自动发布配置表添加账号ID字段
ALTER TABLE `auto_publish_configs`
ADD COLUMN `account_id` varchar(50) DEFAULT NULL COMMENT '关联的脉脉账号ID' AFTER `publish_type`,
ADD KEY `idx_account_id` (`account_id`);

-- 5. 插入默认账号(使用环境变量中的token)
-- 注意: 这条语句需要在应用启动时通过代码执行,因为需要从环境变量读取token
-- INSERT INTO `maimai_accounts` (`id`, `name`, `access_token`, `description`, `is_default`, `is_active`)
-- VALUES ('default', '默认账号', '${MAIMAI_ACCESS_TOKEN}', '从环境变量迁移的默认账号', 1, 1);
