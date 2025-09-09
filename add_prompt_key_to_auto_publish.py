#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为自动发布配置表添加提示词字段的迁移脚本
"""

import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

def add_prompt_key_field():
    """为 auto_publish_configs 表添加 prompt_key 字段"""
    # 直接创建数据库管理器实例
    db = DatabaseManager(
        host='116.205.244.106',
        port=3306,
        user='root',
        password='202358hjq',
        database='maimaichat'
    )
    
    try:
        # 检查字段是否已存在
        check_sql = """
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'auto_publish_configs' 
        AND COLUMN_NAME = 'prompt_key'
        """
        
        result = db.execute_query(check_sql)
        if result and len(result) > 0 and result[0]['count'] > 0:
            logger.info("字段 prompt_key 已存在，跳过添加")
            return True
        
        # 添加字段
        alter_sql = """
        ALTER TABLE `auto_publish_configs` 
        ADD COLUMN `prompt_key` varchar(100) NULL DEFAULT NULL COMMENT '使用的提示词键名' 
        AFTER `topic_id`
        """
        
        db.execute_update(alter_sql)
        logger.info("成功添加 prompt_key 字段到 auto_publish_configs 表")
        
        # 验证字段是否添加成功
        verify_result = db.execute_query(check_sql)
        if verify_result and len(verify_result) > 0 and verify_result[0]['count'] > 0:
            logger.info("字段添加验证成功")
            return True
        else:
            logger.error("字段添加验证失败")
            return False
            
    except Exception as e:
        logger.error(f"添加 prompt_key 字段失败: {e}")
        return False
    finally:
        try:
            db.close_all_connections()
        except:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("开始为自动发布配置表添加提示词字段...")
    success = add_prompt_key_field()
    
    if success:
        print("✓ 数据库迁移完成")
    else:
        print("✗ 数据库迁移失败")