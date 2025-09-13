import requests
import json
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AIContentGenerator:
    """AI内容生成器，支持对话历史模式"""

    def __init__(self, api_config: Dict[str, Any]):
        self.api_key = api_config.get('api_key')
        self.base_url = api_config.get('base_url')
        self.main_model = api_config.get('main_model')
        self.assistant_model = api_config.get('assistant_model')

        if not all([self.api_key, self.base_url, self.main_model]):
            raise ValueError("AI API配置不完整")

    def chat(self,
             messages: List[Dict[str, str]],
             use_main_model: bool = True,
             max_tokens: int = 20000,
             temperature: float = 0.7) -> Dict[str, Any]:
        """
        使用对话历史生成回复

        Args:
            messages: 消息列表，如[{role, content}]
            use_main_model: 是否使用主模型
            max_tokens: 最大生成token
            temperature: 采样温度
        """
        try:
            model = self.main_model if use_main_model else self.assistant_model

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': model,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature
            }
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=600
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data['choices'][0]['message']['content']
                
                # 打印AI真正的原始回答
                logger.info("="*50)
                logger.info("AI真正的原始回答:")
                logger.info(content)
                logger.info("="*50)
                
                return {
                    'success': True,
                    'content': content,  # 直接返回原始内容，不做任何处理
                    'model_used': model,
                    'tokens_used': data.get('usage', {}).get('total_tokens', 0)
                }
            else:
                logger.error(f"AI API请求失败：{resp.status_code} - {resp.text}")
                return {
                    'success': False,
                    'error': f"API请求失败：{resp.status_code}",
                    'details': resp.text
                }
        except requests.exceptions.Timeout:
            logger.error("AI API请求超时")
            return {'success': False, 'error': '请求超时，请稍后重试'}
        except requests.exceptions.RequestException as e:
            logger.error(f"AI API请求异常：{str(e)}")
            return {'success': False, 'error': f'网络请求异常：{str(e)}'}
        except Exception as e:
            logger.error(f"AI对话异常：{str(e)}")
            return {'success': False, 'error': f'生成时发生错误：{str(e)}'}

    def _clean_brackets_content(self, content: str) -> str:
        """
        清理内容中的方括号内容，如[1]、[注释]等
        """
        try:
            # 使用正则表达式删除所有方括号及其内容
            cleaned_content = re.sub(r'\[[^\]]*\]', '', content)
            logger.debug("已清理content中的方括号内容")
            return cleaned_content
        except Exception as e:
            logger.warning(f"清理方括号内容时出错：{e}，返回原内容")
            return content

    def test_connection(self) -> Dict[str, Any]:
        try:
            return self.chat([
                {'role': 'system', 'content': '你是一个简洁助手'},
                {'role': 'user', 'content': "请仅回复：连接成功"}
            ])
        except Exception as e:
            return {'success': False, 'error': f"连接测试失败：{str(e)}"}
