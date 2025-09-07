import requests
import logging
import time
from typing import Dict, Tuple, Optional
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class HttpRequestExecutor:
    """HTTP请求执行器"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        初始化HTTP请求执行器
        
        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # 重试间隔递增因子
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # 创建会话并配置重试
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def execute_request(self, request_config: Dict) -> Tuple[bool, str]:
        """
        执行HTTP请求
        
        Args:
            request_config: 请求配置字典
            
        Returns:
            Tuple[bool, str]: (是否成功, 响应内容或错误信息)
        """
        url = request_config.get('url')
        method = request_config.get('method', 'GET').upper()
        headers = request_config.get('headers', {})
        cookies = request_config.get('cookies', {})
        data = request_config.get('data')
        
        if not url:
            return False, "请求URL不能为空"
        
        try:
            logger.info(f"开始执行HTTP请求: {method} {url}")
            
            # 准备请求参数
            request_kwargs = {
                'url': url,
                'method': method,
                'headers': headers,
                'cookies': cookies,
                'timeout': self.timeout,
                'allow_redirects': True
            }
            
            # 根据请求方法设置数据
            if method in ['POST', 'PUT', 'PATCH'] and data:
                if isinstance(data, dict):
                    # 如果是字典，转换为JSON格式
                    request_kwargs['json'] = data
                    if 'Content-Type' not in headers:
                        headers['Content-Type'] = 'application/json'
                else:
                    # 如果是字符串，作为表单数据发送
                    request_kwargs['data'] = data
                    if 'Content-Type' not in headers:
                        headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            # 记录请求详情
            self._log_request_details(request_kwargs)
            
            # 执行请求
            start_time = time.time()
            response = self.session.request(**request_kwargs)
            execution_time = time.time() - start_time
            
            # 记录响应详情
            self._log_response_details(response, execution_time)
            
            # 检查响应状态
            if response.status_code == 200:
                result_text = f"请求成功 - 状态码: {response.status_code}, 响应时间: {execution_time:.2f}s"
                
                # 尝试获取响应内容的简要信息
                try:
                    content_length = len(response.content)
                    if content_length > 0:
                        result_text += f", 响应大小: {content_length} bytes"
                        
                        # 如果是文本响应，记录前200个字符
                        if response.headers.get('content-type', '').startswith('text/'):
                            preview = response.text[:200]
                            if len(response.text) > 200:
                                preview += "..."
                            result_text += f", 内容预览: {preview}"
                        
                except Exception as e:
                    logger.warning(f"获取响应内容时出错: {e}")
                
                return True, result_text
            else:
                error_msg = f"请求失败 - 状态码: {response.status_code}, 响应时间: {execution_time:.2f}s"
                try:
                    # 尝试获取错误响应内容
                    error_content = response.text[:500] if response.text else "无响应内容"
                    error_msg += f", 错误内容: {error_content}"
                except:
                    pass
                
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"请求超时 (>{self.timeout}秒)"
            logger.error(error_msg)
            return False, error_msg
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"连接错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"执行请求时发生未知错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _log_request_details(self, request_kwargs: Dict):
        """记录请求详情"""
        method = request_kwargs.get('method', 'GET')
        url = request_kwargs.get('url')
        headers = request_kwargs.get('headers', {})
        cookies = request_kwargs.get('cookies', {})
        
        logger.info(f"请求详情 - 方法: {method}, URL: {url}")
        
        if headers:
            logger.debug(f"请求头: {headers}")
        
        if cookies:
            # 只记录cookie的键名，不记录值以保护隐私
            cookie_keys = list(cookies.keys())
            logger.debug(f"Cookies: {cookie_keys}")
        
        if 'json' in request_kwargs:
            logger.debug(f"JSON数据: {request_kwargs['json']}")
        elif 'data' in request_kwargs:
            logger.debug(f"表单数据: {request_kwargs['data']}")
    
    def _log_response_details(self, response: requests.Response, execution_time: float):
        """记录响应详情"""
        logger.info(f"响应详情 - 状态码: {response.status_code}, 耗时: {execution_time:.2f}s")
        
        # 记录响应头的关键信息
        content_type = response.headers.get('content-type')
        content_length = response.headers.get('content-length')
        
        if content_type:
            logger.debug(f"响应类型: {content_type}")
        if content_length:
            logger.debug(f"响应大小: {content_length} bytes")
    
    def test_connection(self, url: str) -> Tuple[bool, str]:
        """
        测试连接是否可达
        
        Args:
            url: 测试的URL
            
        Returns:
            Tuple[bool, str]: (连接是否成功, 结果信息)
        """
        try:
            response = self.session.head(url, timeout=10)
            if response.status_code < 400:
                return True, f"连接成功 - 状态码: {response.status_code}"
            else:
                return False, f"连接失败 - 状态码: {response.status_code}"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"
    
    def close(self):
        """关闭HTTP会话"""
        if self.session:
            self.session.close()
            logger.info("HTTP会话已关闭")