#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行005迁移脚本 - 添加多账号支持
"""

import os
import sys
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database.manager import DatabaseManager

def run_migration():
    """执行迁移"""
    # 数据库配置
    db = DatabaseManager(
        host='116.205.244.106',
        port=3306,
        user='root',
        password='202358hjq',
        database='maimaichat'
    )

    try:
        print("开始执行迁移005 - 添加多账号支持...")

        # 1. 创建账号表
        print("1. 创建maimai_accounts表...")
        db.execute_update("""
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='脉脉账号表'
        """)
        print("✓ maimai_accounts表创建成功")

        # 2. 检查scheduled_posts表是否已有account_id字段
        print("2. 为scheduled_posts表添加account_id字段...")
        try:
            db.execute_update("""
                ALTER TABLE `scheduled_posts`
                ADD COLUMN `account_id` varchar(50) DEFAULT NULL COMMENT '关联的脉脉账号ID' AFTER `publish_type`,
                ADD KEY `idx_account_id` (`account_id`)
            """)
            print("✓ scheduled_posts表account_id字段添加成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ scheduled_posts表account_id字段已存在,跳过")
            else:
                raise

        # 3. 检查drafts表是否已有account_id字段
        print("3. 为drafts表添加account_id字段...")
        try:
            db.execute_update("""
                ALTER TABLE `drafts`
                ADD COLUMN `account_id` varchar(50) DEFAULT NULL COMMENT '关联的脉脉账号ID' AFTER `publish_type`,
                ADD KEY `idx_account_id` (`account_id`)
            """)
            print("✓ drafts表account_id字段添加成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ drafts表account_id字段已存在,跳过")
            else:
                raise

        # 4. 检查auto_publish_configs表是否已有account_id字段
        print("4. 为auto_publish_configs表添加account_id字段...")
        try:
            db.execute_update("""
                ALTER TABLE `auto_publish_configs`
                ADD COLUMN `account_id` varchar(50) DEFAULT NULL COMMENT '关联的脉脉账号ID' AFTER `publish_type`,
                ADD KEY `idx_account_id` (`account_id`)
            """)
            print("✓ auto_publish_configs表account_id字段添加成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ auto_publish_configs表account_id字段已存在,跳过")
            else:
                raise

        # 5. 插入默认账号
        print("5. 插入默认账号...")
        access_token = os.environ.get('MAIMAI_ACCESS_TOKEN', '')

        if access_token:
            # 检查是否已存在默认账号
            existing = db.execute_query("SELECT id FROM maimai_accounts WHERE is_default = 1")

            if not existing:
                account_id = str(uuid.uuid4())
                db.execute_update("""
                    INSERT INTO `maimai_accounts` (`id`, `name`, `access_token`, `description`, `is_default`, `is_active`)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (account_id, '默认账号', access_token, '从环境变量迁移的默认账号', 1, 1))
                print(f"✓ 默认账号创建成功 (ID: {account_id})")
            else:
                print("✓ 默认账号已存在,跳过创建")
        else:
            print("⚠ 警告: 未找到MAIMAI_ACCESS_TOKEN环境变量,跳过默认账号创建")

        print("\n✅ 迁移005执行完成!")
        return True

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
