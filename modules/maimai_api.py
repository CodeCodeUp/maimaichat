import requests
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class MaimaiAPI:
    """脉脉API接口类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化脉脉API
        
        Args:
            config: 脉脉API配置字典
        """
        self.base_url = config.get('base_url', 'https://maimai.cn/api')
        self.access_token = config.get('access_token', '')
        self.user_agent = config.get('user_agent', 'MaimaiChat/1.0')
        
        # 设置请求头
        self.headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.access_token:
            self.headers['Authorization'] = f'Bearer {self.access_token}'
    
    def extract_topic_id(self, url: str) -> Optional[str]:
        """
        从脉脉话题URL中提取topic_id
        
        Args:
            url: 脉脉话题URL
            
        Returns:
            topic_id或None
        """
        try:
            # 解析URL参数
            if 'topic_id=' in url:
                topic_id = url.split('topic_id=')[1].split('&')[0]
                return topic_id
            return None
        except Exception as e:
            logger.error(f"提取topic_id失败：{str(e)}")
            return None
    
    def publish_content(self, 
                       title: str, 
                       content: str, 
                       topic_url: str = "") -> Dict[str, Any]:
        """
        发布内容到脉脉
        
        Args:
            title: 文章标题
            content: 文章内容
            topic_url: 话题URL（可选）
            
        Returns:
            发布结果字典
        """
        try:
            # 构建发布数据
            post_data = {
                'title': title,
                'content': content,
                'type': 'text'  # 文本类型
            }
            
            # 如果有话题URL，提取topic_id
            if topic_url:
                topic_id = self.extract_topic_id(topic_url)
                if topic_id:
                    post_data['topic_id'] = topic_id
                    logger.info(f"关联话题ID：{topic_id}")
            
            # 注意：这里的API端点需要根据实际的脉脉API文档调整
            # 目前使用模拟的端点，实际使用时需要替换为真实的API
            endpoint = f"{self.base_url}/posts"
            
            logger.info(f"准备发布内容到脉脉：{title}")
            
            # 发送发布请求
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"内容发布成功：{title}")
                
                return {
                    'success': True,
                    'message': '发布成功',
                    'post_id': result.get('id', ''),
                    'url': result.get('url', '')
                }
            else:
                logger.error(f"发布失败：{response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"发布失败：HTTP {response.status_code}",
                    'details': response.text
                }
                
        except requests.exceptions.Timeout:
            logger.error("发布请求超时")
            return {
                'success': False,
                'error': "发布请求超时，请稍后重试"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"发布请求异常：{str(e)}")
            return {
                'success': False,
                'error': f"网络请求异常：{str(e)}"
            }
        except Exception as e:
            logger.error(f"发布异常：{str(e)}")
            return {
                'success': False,
                'error': f"发布时发生错误：{str(e)}"
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试脉脉API连接
        
        Returns:
            测试结果字典
        """
        try:
            # 测试用户信息接口（需要根据实际API调整）
            endpoint = f"{self.base_url}/user/profile"
            
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': '脉脉API连接正常'
                }
            else:
                return {
                    'success': False,
                    'error': f"API连接失败：HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"连接测试失败：{str(e)}"
            }
    
    def get_topic_info(self, topic_url: str) -> Dict[str, Any]:
        """
        获取话题信息
        
        Args:
            topic_url: 话题URL
            
        Returns:
            话题信息字典
        """
        try:
            topic_id = self.extract_topic_id(topic_url)
            if not topic_id:
                return {
                    'success': False,
                    'error': '无法从URL中提取话题ID'
                }
            
            # 获取话题信息（需要根据实际API调整）
            endpoint = f"{self.base_url}/topics/{topic_id}"
            
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                topic_data = response.json()
                return {
                    'success': True,
                    'topic_id': topic_id,
                    'title': topic_data.get('title', ''),
                    'description': topic_data.get('description', ''),
                    'participant_count': topic_data.get('participant_count', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f"获取话题信息失败：HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"获取话题信息异常：{str(e)}"
            }
