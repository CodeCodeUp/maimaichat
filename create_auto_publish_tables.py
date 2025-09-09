#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建自动发布模块所需的数据库表
"""

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database.manager import get_db_manager, init_database

def create_auto_publish_tables():
    """创建自动发布模块所需的数据库表"""
    
    # 初始化数据库连接
    print("初始化数据库连接...")
    init_database()
    
    db = get_db_manager()
    
    # 1. 创建自动发布配置表
    print("创建 auto_publish_configs 表...")
    auto_publish_configs_sql = """
    CREATE TABLE IF NOT EXISTS `auto_publish_configs` (
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
      KEY `idx_is_active` (`is_active`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动发布配置表'
    """
    
    try:
        db.execute_update(auto_publish_configs_sql)
        print("✓ auto_publish_configs 表创建成功")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✓ auto_publish_configs 表已存在")
        else:
            print(f"✗ auto_publish_configs 表创建失败: {e}")
            return False
    
    # 2. 创建AI对话历史表
    print("创建 ai_conversations 表...")
    ai_conversations_sql = """
    CREATE TABLE IF NOT EXISTS `ai_conversations` (
      `id` varchar(50) NOT NULL COMMENT '对话ID',
      `topic_id` varchar(50) NOT NULL COMMENT '话题ID',
      `messages` json NOT NULL COMMENT '对话消息历史',
      `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      PRIMARY KEY (`id`),
      KEY `idx_topic_id` (`topic_id`),
      KEY `idx_created_at` (`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话历史表'
    """
    
    try:
        db.execute_update(ai_conversations_sql)
        print("✓ ai_conversations 表创建成功")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✓ ai_conversations 表已存在")
        else:
            print(f"✗ ai_conversations 表创建失败: {e}")
            return False
    
    # 3. 检查并扩展定时发布表
    print("检查 scheduled_posts 表是否需要扩展...")
    try:
        # 检查 auto_publish_id 字段是否存在
        columns = db.execute_query("SHOW COLUMNS FROM scheduled_posts LIKE 'auto_publish_id'")
        if not columns:
            print("为 scheduled_posts 表添加 auto_publish_id 字段...")
            alter_sql = """
            ALTER TABLE `scheduled_posts` 
            ADD COLUMN `auto_publish_id` varchar(50) NULL DEFAULT NULL COMMENT '自动发布配置ID' AFTER `topic_name`,
            ADD KEY `idx_auto_publish_id` (`auto_publish_id`)
            """
            db.execute_update(alter_sql)
            print("✓ scheduled_posts 表扩展成功")
        else:
            print("✓ scheduled_posts 表已包含 auto_publish_id 字段")
    except Exception as e:
        print(f"✗ scheduled_posts 表扩展失败: {e}")
        return False
    
    # 4. 验证表创建结果
    print("\n=== 验证表创建结果 ===")
    tables_to_check = ['auto_publish_configs', 'ai_conversations', 'scheduled_posts']
    
    for table in tables_to_check:
        try:
            result = db.execute_query(f"SHOW TABLES LIKE '{table}'")
            if result:
                columns = db.execute_query(f"DESCRIBE {table}")
                print(f"✓ 表 {table} 存在，包含 {len(columns)} 个字段")
            else:
                print(f"✗ 表 {table} 不存在")
        except Exception as e:
            print(f"✗ 检查表 {table} 失败: {e}")
    
    print("\n=== 数据库表创建完成 ===")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        success = create_auto_publish_tables()
        if success:
            print("✅ 自动发布模块数据库表创建成功！")
            sys.exit(0)
        else:
            print("❌ 数据库表创建失败！")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
