#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移管理器
用于管理和执行数据库迁移脚本
"""

import os
import re
import hashlib
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from modules.database.manager import get_db_manager, init_database_manager

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

class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.db = None
        self.migrations_dir = Path(__file__).parent
        
    def _connect_db(self):
        """连接数据库"""
        if not self.db:
            try:
                self.db = init_database_manager(**DATABASE_CONFIG)
                if not self.db.test_connection():
                    raise Exception("数据库连接失败")
                logger.info("数据库连接成功")
            except Exception as e:
                logger.error(f"数据库连接失败: {e}")
                raise
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件MD5校验和"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"计算校验和失败 {file_path}: {e}")
            return ""
    
    def _ensure_migration_table(self):
        """确保迁移状态表存在"""
        try:
            # 检查表是否存在
            result = self.db.execute_query(
                "SHOW TABLES LIKE 'schema_migrations'"
            )
            
            if not result:
                logger.info("创建迁移状态跟踪表...")
                migration_table_sql = self.migrations_dir / "000_create_migration_table.sql"
                if migration_table_sql.exists():
                    with open(migration_table_sql, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    # 分割并执行SQL语句
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    for stmt in statements:
                        if stmt.upper().startswith(('CREATE', 'INSERT')):
                            self.db.execute_update(stmt)
                    
                    logger.info("迁移状态跟踪表创建成功")
                else:
                    raise Exception("找不到迁移表创建脚本")
            
        except Exception as e:
            logger.error(f"确保迁移表存在失败: {e}")
            raise
    
    def _get_migration_files(self) -> List[Dict]:
        """获取所有迁移文件"""
        try:
            files = []
            pattern = re.compile(r'^(\d{3})_(.+)\.sql$')
            
            for file_path in self.migrations_dir.glob("*.sql"):
                if file_path.name.startswith('000_'):
                    continue  # 跳过迁移表创建脚本
                    
                match = pattern.match(file_path.name)
                if match:
                    version = match.group(1)
                    name = match.group(2)
                    files.append({
                        'version': version,
                        'name': name,
                        'file_path': file_path,
                        'checksum': self._calculate_checksum(file_path)
                    })
            
            # 按版本号排序
            files.sort(key=lambda x: x['version'])
            return files
            
        except Exception as e:
            logger.error(f"获取迁移文件失败: {e}")
            return []
    
    def _get_executed_migrations(self) -> List[Dict]:
        """获取已执行的迁移记录"""
        try:
            return self.db.execute_query(
                "SELECT version, name, executed_at, status, checksum FROM schema_migrations ORDER BY version"
            )
        except Exception as e:
            logger.error(f"获取已执行迁移记录失败: {e}")
            return []
    
    def _execute_migration(self, migration: Dict) -> bool:
        """执行单个迁移"""
        try:
            start_time = time.time()
            
            logger.info(f"执行迁移 {migration['version']}: {migration['name']}")
            
            # 读取迁移文件
            with open(migration['file_path'], 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 移除回滚部分（在注释块中）
            sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
            
            # 分割并执行SQL语句
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for stmt in statements:
                if stmt.upper().startswith(('ALTER', 'CREATE', 'INSERT', 'UPDATE', 'DELETE', 'SELECT', 'SHOW')):
                    try:
                        if stmt.upper().startswith(('SELECT', 'SHOW')):
                            # 对于查询语句，只记录日志
                            result = self.db.execute_query(stmt)
                            if result:
                                logger.debug(f"查询结果: {result}")
                        else:
                            self.db.execute_update(stmt)
                    except Exception as e:
                        # 对于某些可能的错误（如字段已存在），只警告
                        if any(keyword in str(e).lower() for keyword in ['already exists', 'duplicate', 'unknown column']):
                            logger.warning(f"SQL警告（可忽略）: {e}")
                        else:
                            raise
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # 记录迁移执行状态
            self.db.execute_update(
                """
                INSERT INTO schema_migrations 
                (version, name, description, execution_time_ms, checksum, status) 
                VALUES (%s, %s, %s, %s, %s, 'success')
                ON DUPLICATE KEY UPDATE 
                executed_at = NOW(),
                execution_time_ms = VALUES(execution_time_ms),
                checksum = VALUES(checksum),
                status = 'success',
                error_message = NULL
                """,
                (migration['version'], migration['name'], 
                 f"迁移文件: {migration['file_path'].name}",
                 execution_time, migration['checksum'])
            )
            
            logger.info(f"迁移 {migration['version']} 执行成功，耗时 {execution_time}ms")
            return True
            
        except Exception as e:
            logger.error(f"执行迁移 {migration['version']} 失败: {e}")
            
            # 记录失败状态
            try:
                self.db.execute_update(
                    """
                    INSERT INTO schema_migrations 
                    (version, name, description, checksum, status, error_message) 
                    VALUES (%s, %s, %s, %s, 'failed', %s)
                    ON DUPLICATE KEY UPDATE 
                    executed_at = NOW(),
                    checksum = VALUES(checksum),
                    status = 'failed',
                    error_message = VALUES(error_message)
                    """,
                    (migration['version'], migration['name'], 
                     f"迁移文件: {migration['file_path'].name}",
                     migration['checksum'], str(e))
                )
            except Exception as record_error:
                logger.error(f"记录失败状态时出错: {record_error}")
            
            return False
    
    def migrate(self) -> bool:
        """执行所有待迁移的脚本"""
        try:
            self._connect_db()
            self._ensure_migration_table()
            
            # 获取迁移文件和已执行记录
            migration_files = self._get_migration_files()
            executed_migrations = self._get_executed_migrations()
            
            executed_versions = {m['version'] for m in executed_migrations}
            
            logger.info(f"发现 {len(migration_files)} 个迁移文件")
            logger.info(f"已执行 {len(executed_migrations)} 个迁移")
            
            # 找出待执行的迁移
            pending_migrations = [
                m for m in migration_files 
                if m['version'] not in executed_versions
            ]
            
            if not pending_migrations:
                logger.info("所有迁移已是最新状态")
                return True
            
            logger.info(f"需要执行 {len(pending_migrations)} 个待迁移脚本")
            
            # 执行待迁移脚本
            success_count = 0
            for migration in pending_migrations:
                if self._execute_migration(migration):
                    success_count += 1
                else:
                    logger.error(f"迁移失败，停止后续迁移")
                    break
            
            logger.info(f"迁移完成: 成功 {success_count}/{len(pending_migrations)}")
            return success_count == len(pending_migrations)
            
        except Exception as e:
            logger.error(f"迁移过程失败: {e}")
            return False
    
    def status(self):
        """显示迁移状态"""
        try:
            self._connect_db()
            self._ensure_migration_table()
            
            migration_files = self._get_migration_files()
            executed_migrations = self._get_executed_migrations()
            
            print("\n=== 迁移状态 ===")
            print(f"发现迁移文件: {len(migration_files)}")
            print(f"已执行迁移: {len(executed_migrations)}")
            
            executed_dict = {m['version']: m for m in executed_migrations}
            
            print("\n迁移详情:")
            print("版本\t名称\t\t\t\t状态\t\t执行时间")
            print("-" * 80)
            
            for migration in migration_files:
                version = migration['version']
                name = migration['name'][:30]  # 限制长度
                
                if version in executed_dict:
                    executed = executed_dict[version]
                    status = executed['status']
                    executed_at = executed.get('executed_at', 'Unknown')
                    print(f"{version}\t{name:<30}\t{status}\t\t{executed_at}")
                else:
                    print(f"{version}\t{name:<30}\tPENDING\t\t-")
            
            print()
            
        except Exception as e:
            logger.error(f"获取迁移状态失败: {e}")
    
    def rollback(self, target_version: str = None):
        """回滚迁移（暂未实现）"""
        print("回滚功能暂未实现")
        print("如需回滚，请手动执行迁移文件中的回滚脚本（注释部分）")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移管理工具')
    parser.add_argument('command', choices=['migrate', 'status', 'rollback'], help='执行的命令')
    parser.add_argument('--target', help='目标版本（用于回滚）')
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    try:
        if args.command == 'migrate':
            success = manager.migrate()
            sys.exit(0 if success else 1)
        elif args.command == 'status':
            manager.status()
        elif args.command == 'rollback':
            manager.rollback(args.target)
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()