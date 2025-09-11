#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脉脉自动发布系统数据库初始化脚本
"""

import os
import sys
import logging
import pymysql
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from modules.database.manager import init_database_manager, get_db_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_CONFIG = {
    'host': '116.205.244.106',
    'port': 3306,
    'user': 'root',
    'password': '202358hjq',
    'database': 'maimaichat'
}

def read_sql_file(file_path):
    """读取SQL文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取SQL文件失败 {file_path}: {e}")
        return None

def execute_sql_script(sql_content, db_manager):
    """执行SQL脚本"""
    try:
        # 分割SQL语句（以分号分隔）
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        success_count = 0
        for stmt in statements:
            if stmt.upper().startswith(('CREATE', 'INSERT', 'ALTER', 'DROP', 'SET')):
                try:
                    db_manager.execute_update(stmt)
                    success_count += 1
                    logger.debug(f"执行成功: {stmt[:50]}...")
                except Exception as e:
                    # 对于某些可能重复的操作，只警告不中断
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        logger.warning(f"SQL语句已存在，跳过: {e}")
                    else:
                        logger.error(f"执行SQL语句失败: {stmt[:50]}... - {e}")
                        raise
        
        logger.info(f"成功执行 {success_count} 条SQL语句")
        return True
        
    except Exception as e:
        logger.error(f"执行SQL脚本失败: {e}")
        return False

def check_database_exists(config):
    """检查数据库是否存在"""
    try:
        # 不指定数据库连接
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{config['database']}'")
            result = cursor.fetchone()
            return result is not None
            
    except Exception as e:
        logger.error(f"检查数据库存在性失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_database_if_not_exists(config):
    """创建数据库（如果不存在）"""
    try:
        # 不指定数据库连接
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            logger.info(f"数据库 {config['database']} 准备就绪")
            
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def check_tables_exist(db_manager):
    """检查关键表是否存在"""
    try:
        key_tables = [
            'ai_configs', 'topics', 'auto_publish_configs', 
            'scheduled_posts', 'prompts', 'keyword_groups'
        ]
        
        for table in key_tables:
            result = db_manager.execute_query(f"SHOW TABLES LIKE '{table}'")
            if not result:
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"检查表存在性失败: {e}")
        return False

def init_database():
    """初始化数据库"""
    try:
        logger.info("=== 脉脉自动发布系统数据库初始化开始 ===")
        
        # 1. 检查并创建数据库
        logger.info("1. 检查数据库...")
        if not check_database_exists(DATABASE_CONFIG):
            logger.info("数据库不存在，正在创建...")
            create_database_if_not_exists(DATABASE_CONFIG)
        else:
            logger.info("数据库已存在")
        
        # 2. 初始化数据库管理器
        logger.info("2. 初始化数据库连接...")
        db_manager = init_database_manager(**DATABASE_CONFIG)
        
        # 3. 测试连接
        if not db_manager.test_connection():
            raise Exception("数据库连接测试失败")
        logger.info("数据库连接测试成功")
        
        # 4. 检查表是否已存在
        logger.info("3. 检查表结构...")
        if check_tables_exist(db_manager):
            logger.info("主要表已存在，数据库已初始化")
            return True
        
        # 5. 执行数据库schema
        logger.info("4. 创建表结构...")
        schema_path = Path(__file__).parent / 'schema.sql'
        
        if not schema_path.exists():
            raise Exception(f"找不到schema文件: {schema_path}")
        
        sql_content = read_sql_file(schema_path)
        if not sql_content:
            raise Exception("读取schema文件失败")
        
        if not execute_sql_script(sql_content, db_manager):
            raise Exception("执行schema脚本失败")
        
        # 6. 验证初始化结果
        logger.info("5. 验证初始化结果...")
        if not check_tables_exist(db_manager):
            raise Exception("表创建验证失败")
        
        logger.info("=== 数据库初始化完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    try:
        logger.warning("=== 开始重置数据库 ===")
        
        # 初始化连接
        db_manager = init_database_manager(**DATABASE_CONFIG)
        
        # 获取所有表
        tables = db_manager.execute_query("SHOW TABLES")
        table_names = [table[f"Tables_in_{DATABASE_CONFIG['database']}"] for table in tables]
        
        if table_names:
            logger.info(f"发现 {len(table_names)} 个表，准备删除...")
            
            # 禁用外键检查
            db_manager.execute_update("SET FOREIGN_KEY_CHECKS = 0")
            
            # 删除所有表
            for table_name in table_names:
                try:
                    db_manager.execute_update(f"DROP TABLE IF EXISTS `{table_name}`")
                    logger.info(f"已删除表: {table_name}")
                except Exception as e:
                    logger.error(f"删除表 {table_name} 失败: {e}")
            
            # 恢复外键检查
            db_manager.execute_update("SET FOREIGN_KEY_CHECKS = 1")
        
        # 重新初始化
        return init_database()
        
    except Exception as e:
        logger.error(f"重置数据库失败: {e}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='脉脉自动发布系统数据库初始化工具')
    parser.add_argument('--reset', action='store_true', help='重置数据库（删除所有表并重新创建）')
    parser.add_argument('--force', action='store_true', help='强制执行，不提示确认')
    
    args = parser.parse_args()
    
    if args.reset:
        if not args.force:
            confirm = input("⚠️  即将重置数据库，这将删除所有数据！确认继续？(yes/no): ")
            if confirm.lower() != 'yes':
                print("操作已取消")
                return
        
        success = reset_database()
    else:
        success = init_database()
    
    if success:
        print("✅ 数据库操作完成")
        sys.exit(0)
    else:
        print("❌ 数据库操作失败")
        sys.exit(1)

if __name__ == '__main__':
    main()