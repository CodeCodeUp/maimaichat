#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为scheduled_posts表添加auto_publish_id字段
"""

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database.manager import get_db_manager, init_database_manager
from modules.database.init import init_database_from_config

def add_auto_publish_field():
    """为scheduled_posts表添加auto_publish_id字段"""
    
    # 初始化数据库连接
    print("初始化数据库连接...")
    init_database_from_config()
    
    db = get_db_manager()
    
    try:
        # 检查字段是否已存在
        print("检查 auto_publish_id 字段是否已存在...")
        columns = db.execute_query("SHOW COLUMNS FROM scheduled_posts LIKE 'auto_publish_id'")
        
        if columns:
            print("✓ auto_publish_id 字段已存在，无需添加")
            return True
        
        print("添加 auto_publish_id 字段到 scheduled_posts 表...")
        
        # 添加字段的SQL
        alter_sql = """
        ALTER TABLE `scheduled_posts` 
        ADD COLUMN `auto_publish_id` varchar(50) NULL DEFAULT NULL COMMENT '自动发布配置ID' AFTER `topic_name`,
        ADD KEY `idx_auto_publish_id` (`auto_publish_id`)
        """
        
        db.execute_update(alter_sql)
        print("✓ auto_publish_id 字段添加成功")
        
        # 验证字段添加结果
        columns_after = db.execute_query("SHOW COLUMNS FROM scheduled_posts LIKE 'auto_publish_id'")
        if columns_after:
            print("✓ 字段验证成功")
            return True
        else:
            print("✗ 字段验证失败")
            return False
            
    except Exception as e:
        print(f"✗ 添加字段失败: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        success = add_auto_publish_field()
        if success:
            print("✅ auto_publish_id 字段添加完成！")
            sys.exit(0)
        else:
            print("❌ 字段添加失败！")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
