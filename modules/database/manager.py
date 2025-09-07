import pymysql
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Union
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str, charset: str = 'utf8mb4'):
        """
        初始化数据库连接管理器
        
        Args:
            host: 数据库主机地址
            port: 端口号
            user: 用户名
            password: 密码
            database: 数据库名
            charset: 字符集
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self._local = threading.local()
        self._pool_lock = threading.Lock()
        
        # 连接池配置
        self.max_connections = 10
        self.connection_pool = []
        
        logger.info(f"初始化数据库连接管理器: {user}@{host}:{port}/{database}")
    
    def _create_connection(self) -> pymysql.Connection:
        """创建新的数据库连接"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                autocommit=False,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
            logger.debug("创建新的数据库连接")
            return connection
        except Exception as e:
            logger.error(f"创建数据库连接失败: {e}")
            raise
    
    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接"""
        # 首先检查当前线程是否已有连接
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                # 测试连接是否有效
                self._local.connection.ping(reconnect=True)
                return self._local.connection
            except:
                # 连接无效，清除并创建新连接
                self._local.connection = None
        
        # 从连接池获取连接
        with self._pool_lock:
            if self.connection_pool:
                connection = self.connection_pool.pop()
                try:
                    connection.ping(reconnect=True)
                    self._local.connection = connection
                    return connection
                except:
                    # 连接无效，创建新连接
                    pass
        
        # 创建新连接
        connection = self._create_connection()
        self._local.connection = connection
        return connection
    
    def return_connection(self, connection: pymysql.Connection):
        """归还连接到连接池"""
        if not connection:
            return
        
        try:
            # 回滚未提交的事务
            if connection.open:
                connection.rollback()
            
            with self._pool_lock:
                if len(self.connection_pool) < self.max_connections:
                    self.connection_pool.append(connection)
                    logger.debug("连接归还到连接池")
                else:
                    connection.close()
                    logger.debug("连接池已满，关闭连接")
        except Exception as e:
            logger.warning(f"归还连接时出错: {e}")
            try:
                connection.close()
            except:
                pass
    
    @contextmanager
    def get_cursor(self, autocommit: bool = False):
        """获取数据库游标的上下文管理器"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if autocommit:
                connection.autocommit(True)
            
            yield cursor
            
            if not autocommit:
                connection.commit()
                
        except Exception as e:
            if connection and not autocommit:
                try:
                    connection.rollback()
                except:
                    pass
            logger.error(f"数据库操作异常: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and autocommit:
                connection.autocommit(False)
    
    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行查询SQL"""
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            logger.debug(f"执行查询: {sql}, 参数: {params}, 结果行数: {len(result)}")
            return result
    
    def execute_update(self, sql: str, params: tuple = None) -> int:
        """执行更新SQL"""
        with self.get_cursor() as cursor:
            affected_rows = cursor.execute(sql, params)
            logger.debug(f"执行更新: {sql}, 参数: {params}, 影响行数: {affected_rows}")
            return affected_rows
    
    def execute_insert(self, sql: str, params: tuple = None) -> int:
        """执行插入SQL"""
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            insert_id = cursor.lastrowid
            logger.debug(f"执行插入: {sql}, 参数: {params}, 插入ID: {insert_id}")
            return insert_id
    
    def execute_batch(self, sql: str, params_list: List[tuple]) -> int:
        """批量执行SQL"""
        with self.get_cursor() as cursor:
            affected_rows = cursor.executemany(sql, params_list)
            logger.debug(f"批量执行: {sql}, 批次数: {len(params_list)}, 总影响行数: {affected_rows}")
            return affected_rows
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info("数据库连接测试成功")
                return result is not None
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def create_database_if_not_exists(self):
        """创建数据库（如果不存在）"""
        try:
            # 连接到服务器但不指定数据库
            temp_connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset=self.charset,
                autocommit=True
            )
            
            with temp_connection.cursor() as cursor:
                # 检查数据库是否存在
                cursor.execute("SHOW DATABASES LIKE %s", (self.database,))
                if not cursor.fetchone():
                    # 创建数据库
                    cursor.execute(f"CREATE DATABASE `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"创建数据库: {self.database}")
                else:
                    logger.info(f"数据库已存在: {self.database}")
            
            temp_connection.close()
            
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            raise
    
    def execute_sql_file(self, sql_file_path: str):
        """执行SQL文件"""
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with self.get_cursor(autocommit=True) as cursor:
                for sql in sql_statements:
                    if sql and not sql.startswith('--'):
                        cursor.execute(sql)
                        logger.debug(f"执行SQL: {sql[:100]}...")
            
            logger.info(f"成功执行SQL文件: {sql_file_path}")
            
        except Exception as e:
            logger.error(f"执行SQL文件失败: {e}")
            raise
    
    def close_all_connections(self):
        """关闭所有连接"""
        with self._pool_lock:
            for connection in self.connection_pool:
                try:
                    connection.close()
                except:
                    pass
            self.connection_pool.clear()
        
        # 清理当前线程连接
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
            except:
                pass
            self._local.connection = None
        
        logger.info("所有数据库连接已关闭")


# 全局数据库管理器实例
db_manager: Optional[DatabaseManager] = None

def init_database_manager(host: str, port: int, user: str, password: str, database: str) -> DatabaseManager:
    """初始化全局数据库管理器"""
    global db_manager
    db_manager = DatabaseManager(host, port, user, password, database)
    return db_manager

def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器实例"""
    if db_manager is None:
        raise RuntimeError("数据库管理器尚未初始化")
    return db_manager

# JSON辅助函数
def json_serialize(obj) -> str:
    """JSON序列化辅助函数"""
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, ensure_ascii=False, default=str)

def json_deserialize(json_str) -> Any:
    """JSON反序列化辅助函数"""
    if json_str is None or json_str == '':
        return None
    if isinstance(json_str, (dict, list)):
        return json_str
    try:
        return json.loads(json_str)
    except:
        return json_str

# 时间辅助函数
def format_datetime(dt) -> Optional[str]:
    """格式化datetime为字符串"""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)

def parse_datetime(dt_str) -> Optional[datetime]:
    """解析datetime字符串"""
    if dt_str is None or dt_str == '':
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        return None