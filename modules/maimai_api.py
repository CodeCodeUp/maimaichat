import requests
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urlencode
import urllib.parse
import uuid
import hashlib
import time

logger = logging.getLogger(__name__)

class MaimaiAPI:
    """脉脉API接口类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化脉脉API
        
        Args:
            config: 脉脉API配置字典
        """
        self.base_url = config.get('base_url', 'https://api.taou.com')
        self.access_token = config.get('access_token', '')
        
        # 从配置中获取设备参数和请求头
        self.device_params = config.get('device_params', {})
        self.headers = config.get('headers', {})
    
    def extract_topic_id(self, url: str) -> Optional[str]:
        """
        从脉脉话题URL中提取topic_id
        支持两种URL格式：
        1. 简单格式：https://maimai.cn/n/content/global-topic?circle_type=9&topic_id=zGMekSRN
        2. 复杂格式：发布接口中的topics参数
        
        Args:
            url: 脉脉话题URL
            
        Returns:
            topic_id或None
        """
        try:
            # 方式1：处理简单的话题URL格式
            if 'topic_id=' in url:
                topic_id = url.split('topic_id=')[1].split('&')[0]
                # URL解码
                topic_id = urllib.parse.unquote(topic_id)
                logger.info(f"从简单URL格式提取到topic_id: {topic_id}")
                return topic_id
                
            # 方式2：尝试从复杂的topics参数中解析
            if 'topics=' in url:
                topics_param = url.split('topics=')[1].split('&')[0]
                topics_decoded = urllib.parse.unquote(topics_param)
                try:
                    topics_data = json.loads(topics_decoded)
                    if isinstance(topics_data, list) and len(topics_data) > 0:
                        topic_id = topics_data[0].get('id')
                        logger.info(f"从复杂URL格式提取到topic_id: {topic_id}")
                        return topic_id
                except json.JSONDecodeError:
                    pass
                    
            return None
        except Exception as e:
            logger.error(f"提取topic_id失败：{str(e)}")
            return None
    
    def extract_circle_type(self, url: str) -> int:
        """
        从话题URL中提取circle_type
        
        Args:
            url: 话题URL
            
        Returns:
            circle_type，默认为9
        """
        try:
            if 'circle_type=' in url:
                circle_type = url.split('circle_type=')[1].split('&')[0]
                return int(circle_type)
        except Exception as e:
            logger.warning(f"提取circle_type失败：{str(e)}")
        return 9  # 默认值
    
    def extract_topic_name_from_page(self, topic_url: str) -> Optional[str]:
        """
        从话题页面中解析话题名称
        
        Args:
            topic_url: 话题URL
            
        Returns:
            话题名称或None
        """
        try:
            # 获取话题信息
            topic_info = self.get_topic_info(topic_url)
            if topic_info.get('success'):
                title = topic_info.get('title', '')
                # 移除 " - 脉脉" 后缀
                if title.endswith(' - 脉脉'):
                    title = title[:-4]
                return title
            return None
        except Exception as e:
            logger.error(f"从页面解析话题名称失败：{str(e)}")
            return None
    
    def extract_topic_info_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从脉脉话题URL中提取完整话题信息
        
        Args:
            url: 脉脉话题URL
            
        Returns:
            话题信息字典或None
        """
        try:
            # 尝试从topics参数中解析完整信息
            if 'topics=' in url:
                topics_param = url.split('topics=')[1].split('&')[0]
                topics_decoded = urllib.parse.unquote(topics_param)
                try:
                    topics_data = json.loads(topics_decoded)
                    if isinstance(topics_data, list) and len(topics_data) > 0:
                        return topics_data[0]
                except json.JSONDecodeError:
                    pass
                    
            return None
        except Exception as e:
            logger.error(f"提取话题信息失败：{str(e)}")
            return None
    
    def publish_content(self, 
                       title: str, 
                       content: str, 
                       topic_url: str = None,
                       topic_id: str = None,
                       circle_type: str = None,
                       topic_name: str = None) -> Dict[str, Any]:
        """
        发布内容到脉脉（完全基于真实的移动端API请求）
        
        Args:
            title: 文章标题（可选，主要内容在content中）
            content: 要发布的内容
            topic_url: 话题URL（可选，与topic_id二选一）
            topic_id: 话题ID（可选，与topic_url二选一）
            circle_type: 圈子类型（当使用topic_id时必填）
            topic_name: 话题名称（当使用topic_id时传入，避免重新查询）
            
        Returns:
            发布结果字典
        """
        # 验证参数：topic_url 或 (topic_id + circle_type) 必须提供其中一种
        if topic_url:
            # 使用话题链接模式，从URL提取话题信息
            extracted_topic_id = self.extract_topic_id(topic_url)
            if not extracted_topic_id:
                return {
                    'success': False,
                    'error': '无法从话题URL中提取话题ID'
                }
            final_topic_id = extracted_topic_id
            final_circle_type = str(self.extract_circle_type(topic_url))
            logger.info(f"从URL提取话题信息 - ID: {final_topic_id}, circle_type: {final_circle_type}")
        elif topic_id and circle_type:
            # 使用直接传参模式
            final_topic_id = topic_id
            final_circle_type = str(circle_type)
            logger.info(f"使用传入话题信息 - ID: {final_topic_id}, circle_type: {final_circle_type}")
        else:
            # 无话题发布
            logger.warning("未提供话题信息，尝试无话题发布")
            final_topic_id = None
            final_circle_type = None
        
        try:
            # 构建URL参数（使用配置中的设备参数）
            url_params = self.device_params.copy()
            url_params['access_token'] = f'1.{self.access_token}'
            
            # 添加动态参数
            url_params['launch_uuid'] = str(uuid.uuid4())
            url_params['session_uuid'] = str(uuid.uuid4()).replace('-', '')
            url_params['aigc_rewrite'] = '[]'
            url_params['topics'] = '[]'  # 默认空话题
            url_params['pub_setting'] = '{"cmty_identity":1}'
            url_params['pub_extra'] = '{"post_topics":[]}'
            
            # 如果有话题信息，构造话题参数
            if final_topic_id and final_circle_type:
                try:
                    # 如果是从URL提取的，尝试获取话题名称
                    if topic_url:
                        topic_name = self.extract_topic_name_from_page(topic_url)
                        
                        # 优先尝试从复杂URL格式中提取完整话题信息
                        if 'topics=' in topic_url:
                            try:
                                topics_param = topic_url.split('topics=')[1].split('&')[0]
                                topics_decoded = urllib.parse.unquote(topics_param)
                                # 直接使用解码后的话题数据
                                url_params['topics'] = topics_decoded
                                
                                # 同时更新pub_extra
                                topics_data = json.loads(topics_decoded)
                                url_params['pub_extra'] = json.dumps({"post_topics": topics_data}, ensure_ascii=False)
                                
                                logger.info(f"提取到完整话题信息，话题数量：{len(topics_data)}")
                            except Exception as e:
                                logger.warning(f"解析复杂话题信息失败，使用基础话题信息：{str(e)}")
                                # 构造基础话题数据结构
                                topic_info = {
                                    "id": final_topic_id,
                                    "name": topic_name or f"话题_{final_topic_id}",
                                    "circle_type": int(final_circle_type)
                                }
                                topics_data = [topic_info]
                                url_params['topics'] = json.dumps(topics_data, ensure_ascii=False)
                                url_params['pub_extra'] = json.dumps({"post_topics": topics_data}, ensure_ascii=False)
                        else:
                            # 构造基础话题数据结构
                            topic_info = {
                                "id": final_topic_id,
                                "name": topic_name or f"话题_{final_topic_id}",
                                "circle_type": int(final_circle_type)
                            }
                            topics_data = [topic_info]
                            url_params['topics'] = json.dumps(topics_data, ensure_ascii=False)
                            url_params['pub_extra'] = json.dumps({"post_topics": topics_data}, ensure_ascii=False)
                            
                            logger.info(f"构造话题信息成功 - ID: {final_topic_id}, Name: {topic_name}, CircleType: {final_circle_type}")
                    else:
                        # 使用传入的话题ID和circle_type（来自话题选择）
                        topic_info = {
                            "id": final_topic_id,
                            "name": topic_name or f"话题_{final_topic_id}",  # 优先使用传入的真实名称
                            "circle_type": int(final_circle_type)
                        }
                        topics_data = [topic_info]
                        url_params['topics'] = json.dumps(topics_data, ensure_ascii=False)
                        url_params['pub_extra'] = json.dumps({"post_topics": topics_data}, ensure_ascii=False)
                        
                        logger.info(f"使用选择的话题信息 - ID: {final_topic_id}, Name: {topic_name}, CircleType: {final_circle_type}")
                except Exception as e:
                    logger.warning(f"处理话题信息失败：{str(e)}")
            
            # 构建完整URL
            endpoint = f"{self.base_url}/sdk/publish"
            full_url = f"{endpoint}?{urlencode(url_params)}"
            
            # 构建POST数据（复制真实请求的格式）
            post_data = {
                'annoy_type': '5',
                'is_original': '0',
                'extra_infomation': json.dumps({
                    "aigc_rewrite": "[]",
                    "topics": url_params['topics'],
                    "pub_setting": '{"cmty_identity":1}',
                    "pub_extra": url_params['pub_extra']
                }, ensure_ascii=False),
                'username_type': '5',
                'at_users': '{}',
                'fr': 'topic_detail' if final_topic_id else 'mainpage_701_101',
                'container_id': '-4001',
                'content': content,  # 这里是实际要发布的内容
                'hash': str(int(time.time() * 1000)),
                'target': 'topic_detail_post_pub' if final_topic_id else 'post_pub'
            }
            
            # 如果有标题，添加title字段
            if title and title.strip():
                post_data['title'] = title.strip()
                logger.info(f"添加标题: {title}")
            
            logger.info(f"准备发布内容到脉脉")
            logger.info(f"内容长度：{len(content)}")
            if title:
                logger.info(f"标题：{title}")
            
            # 发送请求（使用真实的请求头）
            response = requests.post(
                full_url,
                headers=self.headers,
                data=urlencode(post_data),
                timeout=30
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text[:200]}...")
            
            # 处理响应
            if response.status_code in [200, 201]:
                try:
                    result = response.json() 
                    logger.info(f"内容发布成功")
                    return {
                        'success': True,
                        'message': '发布成功',
                        'data': result
                    }
                except json.JSONDecodeError:
                    # 非JSON响应但状态码正常
                    logger.info(f"内容发布成功（非JSON响应）")
                    return {
                        'success': True,
                        'message': '发布成功',
                        'data': response.text
                    }
            else:
                logger.error(f"发布失败：{response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"发布失败：HTTP {response.status_code}",
                    'details': response.text
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
            # 构建测试URL参数（使用配置中的设备参数）
            url_params = self.device_params.copy()
            url_params['access_token'] = f"1.{self.access_token}"
            
            # 测试用户信息接口
            endpoint = f"{self.base_url}/sdk/profile"
            full_url = f"{endpoint}?{urlencode(url_params)}"
            
            response = requests.get(
                full_url,
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
