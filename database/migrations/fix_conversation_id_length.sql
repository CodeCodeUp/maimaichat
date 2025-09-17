-- 修复对话ID长度问题
ALTER TABLE `ai_conversations` MODIFY COLUMN `id` varchar(100) NOT NULL COMMENT '对话ID';