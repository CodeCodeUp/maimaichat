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
            
            # 处理响应，不假设一定返回JSON
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    logger.info(f"内容发布成功：{title}")
                    
                    return {
                        'success': True,
                        'message': '发布成功',
                        'post_id': result.get('id', ''),
                        'url': result.get('url', '')
                    }
                except json.JSONDecodeError:
                    # 如果响应不是JSON，但状态码正常，认为发布成功
                    logger.warning(f"发布响应不是JSON格式：{response.text}")
                    logger.info(f"内容发布成功：{title}（非JSON响应）")
                    return {
                        'success': True,
                        'message': '发布成功',
                        'post_id': '',
                        'url': ''
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
        except json.JSONDecodeError as e:
            logger.error(f"发布响应JSON解析失败：{str(e)}")
            return {
                'success': False,
                'error': f"响应格式错误：{str(e)}"
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
                logger.error(f"无法从URL中提取话题ID: {topic_url}")
                return {
                    'success': False,
                    'error': '无法从URL中提取话题ID'
                }
            
            logger.info(f"开始获取话题信息，topic_id: {topic_id}")
            logger.info(f"请求URL: {topic_url}")
            
            # 直接访问话题页面获取信息
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            logger.info(f"发送请求头: {headers}")
            
            response = requests.get(
                topic_url,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                html_content = response.text
                logger.info(f"HTML内容长度: {len(html_content)}")
                logger.info(f"HTML内容前500字符: {html_content[:500]}")
                
                # 尝试从HTML中解析话题信息
                topic_info = self._parse_topic_from_html(html_content, topic_id)
                
                if topic_info:
                    logger.info(f"成功解析话题信息: {topic_info}")
                    return {
                        'success': True,
                        'topic_id': topic_id,
                        'title': topic_info.get('title', f'话题 {topic_id}'),
                        'description': topic_info.get('description', '话题信息获取成功'),
                        'url': topic_url,
                        'participant_count': topic_info.get('participant_count', 0),
                        'status': '页面访问正常'
                    }
                else:
                    logger.warning("无法从HTML中解析话题信息，返回默认信息")
                    return {
                        'success': True,
                        'topic_id': topic_id,
                        'title': f'话题 {topic_id}',
                        'description': '话题信息获取成功，但无法解析详细内容',
                        'url': topic_url,
                        'participant_count': 0,
                        'status': '页面访问正常但解析失败'
                    }
            else:
                logger.error(f"获取话题页面失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text[:200]}")
                return {
                    'success': False,
                    'error': f"获取话题信息失败：HTTP {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("获取话题信息超时")
            return {
                'success': False,
                'error': '获取话题信息超时'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            return {
                'success': False,
                'error': f"网络请求异常：{str(e)}"
            }
        except Exception as e:
            logger.error(f"获取话题信息异常: {str(e)}")
            return {
                'success': False,
                'error': f"获取话题信息异常：{str(e)}"
            }
    
    def _parse_topic_from_html(self, html_content: str, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        从HTML内容中解析话题信息
        
        Args:
            html_content: HTML内容
            topic_id: 话题ID
            
        Returns:
            解析出的话题信息或None
        """
        try:
            import re
            
            logger.info("开始解析HTML内容")
            
            # 尝试解析标题
            title_patterns = [
                r'<title[^>]*>([^<]+)</title>',
                r'<h1[^>]*>([^<]+)</h1>',
                r'<h2[^>]*>([^<]+)</h2>',
                r'"title"\s*:\s*"([^"]+)"',
                r'data-title="([^"]+)"'
            ]
            
            title = None
            for pattern in title_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    logger.info(f"找到标题（模式: {pattern}）: {title}")
                    break
            
            # 尝试解析描述
            desc_patterns = [
                r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
                r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']',
                r'"description"\s*:\s*"([^"]+)"',
                r'<p[^>]*class="[^"]*desc[^"]*"[^>]*>([^<]+)</p>'
            ]
            
            description = None
            for pattern in desc_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    logger.info(f"找到描述（模式: {pattern}）: {description}")
                    break
            
            # 尝试解析参与人数
            participant_patterns = [
                r'参与[^0-9]*(\d+)',
                r'(\d+)[^0-9]*人参与',
                r'"participant_count"\s*:\s*(\d+)',
                r'participant[^0-9]*(\d+)'
            ]
            
            participant_count = 0
            for pattern in participant_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    participant_count = int(match.group(1))
                    logger.info(f"找到参与人数（模式: {pattern}）: {participant_count}")
                    break
            
            # 如果找到了任何信息，返回结果
            if title or description or participant_count > 0:
                result = {
                    'title': title or f'话题 {topic_id}',
                    'description': description or '暂无描述',
                    'participant_count': participant_count
                }
                logger.info(f"解析结果: {result}")
                return result
            else:
                logger.warning("未能从HTML中解析出任何话题信息")
                return None
                
        except Exception as e:
            logger.error(f"解析HTML异常: {str(e)}")
            return None
