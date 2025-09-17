#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动发布生成器 - 完全自动化的循环生成发布系统
"""

import logging
import json
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from modules.database.manager import get_db_manager
from modules.ai.generator import AIContentGenerator
from modules.database.dao import AutoPublishConfigDAO, AIConversationDAO, ScheduledPostDAO, TopicDAO

logger = logging.getLogger(__name__)

class AutoPublishCycleGenerator:
    """自动发布循环生成器"""
    
    def __init__(self):
        self.db = get_db_manager()
        
        # 获取当前AI配置
        from modules.ai.config_store import AIConfigStoreDB
        ai_config_store = AIConfigStoreDB()
        current_config_id = ai_config_store.get_current_config_id()
        current_config = ai_config_store.get_config(current_config_id) if current_config_id else None
        
        if not current_config:
            logger.error("无法获取当前AI配置")
            raise RuntimeError("AI配置未设置，无法初始化自动发布生成器")
        
        self.ai_generator = AIContentGenerator(current_config)
        self.auto_config_dao = AutoPublishConfigDAO()
        self.conversation_dao = AIConversationDAO()
        self.scheduled_post_dao = ScheduledPostDAO()
        self.topic_dao = TopicDAO()
        
        # 添加提示词存储的引用
        from modules.database.stores import PromptStoreDB
        self.prompt_store = PromptStoreDB()
    
    def start_auto_publish_cycle(self, config_id: str) -> bool:
        """
        启动自动发布循环
        配置后立即生成第一篇内容
        """
        try:
            logger.info(f"尝试启动自动发布循环，配置ID: {config_id}")
            
            # 获取配置
            config = self.auto_config_dao.find_by_id(config_id)
            if not config:
                logger.error(f"找不到自动发布配置: {config_id}")
                return False
            
            logger.info(f"获取到配置: {config}")
            
            # 检查是否已达到最大发布数量
            if not self._should_continue_publishing(config):
                logger.info(f"配置 {config_id} 已达到最大发布数量，停止生成")
                return False
            
            logger.info(f"开始生成第一篇内容...")
            
            # 立即生成第一篇内容
            success = self._generate_and_schedule_content(config)
            if success:
                logger.info(f"自动发布循环已启动，配置ID: {config_id}")
            else:
                logger.error(f"生成内容失败，配置ID: {config_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"启动自动发布循环失败: {e}", exc_info=True)
            return False
    
    def continue_auto_publish_cycle(self, config_id: str) -> bool:
        """
        继续自动发布循环
        发布完成后调用此方法生成下一篇
        """
        try:
            # 获取配置
            config = self.auto_config_dao.find_by_id(config_id)
            if not config or not config.get('is_active'):
                logger.info(f"配置 {config_id} 已停用，终止循环")
                return False
            
            # 检查是否应该继续发布
            if not self._should_continue_publishing(config):
                logger.info(f"配置 {config_id} 已达到最大发布数量，终止循环")
                # 自动停用配置
                self.auto_config_dao.update(config_id, {'is_active': 0})
                return False
            
            # 生成下一篇内容
            success = self._generate_and_schedule_content(config)
            if success:
                logger.info(f"自动发布循环继续，生成下一篇内容，配置ID: {config_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"继续自动发布循环失败: {e}")
            return False
    
    def _should_continue_publishing(self, config: Dict[str, Any]) -> bool:
        """检查是否应该继续发布"""
        max_posts = config.get('max_posts', -1)
        current_posts = config.get('current_posts', 0)
        
        # -1 表示无限制
        if max_posts == -1:
            return True
        
        return current_posts < max_posts
    
    def _generate_and_schedule_content(self, config: Dict[str, Any]) -> bool:
        """生成内容并安排发布"""
        try:
            topic_id = config['topic_id']
            config_id = config['id']
            
            # 获取话题信息
            topic = self.topic_dao.find_by_id(topic_id)
            if not topic:
                logger.error(f"找不到话题: {topic_id}")
                return False
            
            # 获取或创建AI对话历史
            conversation = self._get_or_create_conversation(topic_id, config)
            
            # 生成内容
            content_data = self._generate_content_with_history(topic, conversation, config)
            if not content_data:
                logger.error(f"生成内容失败，话题ID: {topic_id}")
                return False
            
            # 计算随机发布时间（使用配置的间隔）
            min_interval = config.get('min_interval', 30)
            max_interval = config.get('max_interval', 60)
            minutes = random.randint(min_interval, max_interval)
            scheduled_at = datetime.now() + timedelta(minutes=minutes)
            logger.info(f"使用配置间隔 {min_interval}-{max_interval} 分钟，随机延迟 {minutes} 分钟")
            
            # 生成唯一的任务ID
            import uuid
            post_id = f"auto_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
            
            # 创建定时发布任务
            # 使用解析出的标题，如果没有标题则使用话题名称
            post_title = content_data.get('title') or ""
            
            post_data = {
                'id': post_id,
                'title': post_title,
                'content': content_data['content'],
                'topic_id': topic_id,
                'circle_type': topic.get('circle_type', ''),
                'topic_name': topic['name'],
                'publish_type': config.get('publish_type', 'anonymous'),  # 从配置中获取发布方式
                'auto_publish_id': config_id,  # 标记为自动发布
                'status': 'pending',
                'scheduled_at': scheduled_at
            }
            
            result_id = self.scheduled_post_dao.insert(post_data)
            if result_id:
                logger.info(f"已安排自动发布任务，{minutes}分钟后发布，任务ID: {post_id}")
                
                # 更新对话历史
                self._update_conversation_history(conversation['id'], content_data['messages'])
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"生成并安排内容失败: {e}")
            return False
    
    def _get_or_create_conversation(self, topic_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """获取或创建AI对话历史（基于配置ID）"""
        try:
            config_id = config['id']

            # 优先根据配置ID查找现有对话
            conversation = self.conversation_dao.get_latest_by_config(config_id)

            if not conversation:
                # 生成更短的对话ID（避免超过数据库字段长度限制）
                import hashlib
                short_config_id = hashlib.md5(config_id.encode()).hexdigest()[:8]
                conversation_id = f"auto_{short_config_id}_{int(datetime.now().timestamp())}"
                initial_messages = []  # 空的消息列表，system消息将在第一次生成时添加

                self.conversation_dao.create_with_messages(conversation_id, topic_id, initial_messages, config_id)
                conversation = self.conversation_dao.find_by_id(conversation_id)
                logger.info(f"为配置 {config_id} 创建了新对话，ID: {conversation_id}")
            else:
                logger.info(f"找到配置 {config_id} 的现有对话: {conversation['id']}")

            return conversation

        except Exception as e:
            logger.error(f"获取或创建对话历史失败: {e}")
            return None
    
    def _generate_content_with_history(self, topic: Dict[str, Any], conversation: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """基于对话历史生成内容"""
        try:
            # 获取历史消息
            messages = conversation.get('messages', [])
            
            # 如果messages是字符串，需要解析JSON
            if isinstance(messages, str):
                import json
                try:
                    messages = json.loads(messages)
                    logger.info(f"成功解析messages JSON，包含 {len(messages)} 条消息")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"解析messages JSON失败: {e}，使用空列表")
                    messages = []
            
            # 确保messages是列表
            if not isinstance(messages, list):
                logger.warning(f"messages类型不正确: {type(messages)}，使用空列表")
                messages = []
            
            # 获取配置中指定的提示词
            prompt_key = config.get('prompt_key')
            if prompt_key:
                base_prompt = self.prompt_store.get_prompt(prompt_key)
                if base_prompt:
                    logger.info(f"使用配置中指定的提示词: {prompt_key}")
                else:
                    # 如果指定的提示词不存在，使用当前选定的提示词作为后备
                    current_prompt_key, current_prompt_content = self.prompt_store.get_current_prompt()
                    if current_prompt_content:
                        base_prompt = current_prompt_content
                        logger.warning(f"指定的提示词 {prompt_key} 不存在，使用当前提示词: {current_prompt_key}")
                    else:
                        base_prompt = "你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。"
                        logger.warning("指定的提示词和当前提示词都不存在，使用默认提示词")
            else:
                # 如果配置中没有指定提示词，使用当前选定的提示词
                current_prompt_key, current_prompt_content = self.prompt_store.get_current_prompt()
                if current_prompt_content:
                    base_prompt = current_prompt_content
                    logger.info(f"配置未指定提示词，使用当前选定的提示词: {current_prompt_key}")
                else:
                    base_prompt = "你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。"
                    logger.warning("配置未指定提示词且当前提示词不存在，使用默认提示词")

            # 同步历史对话中的提示词，确保与当前提示词一致
            messages = self._sync_system_prompt(messages, base_prompt)

            # 检查是否已有system消息，避免重复添加提示词
            has_system_message = any(msg.get('role') == 'system' for msg in messages)

            # 构建用户提示词
            if not has_system_message:
                # 第一次或者没有system消息时，添加完整的提示词作为system消息
                system_message = {
                    "role": "system",
                    "content": base_prompt
                }
                messages.insert(0, system_message)
                user_prompt = "开始"
                logger.info("添加了system消息和第一次创作请求")
            else:
                # 已有历史对话时，只添加简单的继续请求，避免重复提示词
                user_prompt = "开始"
                logger.info("使用简化的继续创作请求，避免重复提示词")
            
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            # 调用AI生成
            response = self.ai_generator.chat(messages, use_main_model=True)
            
            if response and response.get('success'):
                generated_content = response['content']
                
                # 尝试解析内容，直接提取title和content
                title = None
                content = generated_content
                
                try:
                    # 使用统一的简化解析逻辑
                    parsed_result = self._parse_ai_response_simple(generated_content)
                    
                    if parsed_result['success'] and parsed_result['items']:
                        # 使用第一个有效的对象
                        first_item = parsed_result['items'][0]
                        title = first_item['title']
                        content = first_item['content']
                        logger.info(f"成功解析内容 - 标题: {title[:20] if title else 'None'}...")
                    else:
                        # 解析失败，使用原始内容
                        content = generated_content
                        logger.info("未找到title和content，使用原始内容")
                        
                except Exception as e:
                    # 解析失败，使用原始内容
                    content = generated_content
                    logger.warning(f"解析异常: {e}，使用原始内容")
                
                # 添加AI回复到历史
                messages.append({
                    "role": "assistant",
                    "content": generated_content
                })
                
                return {
                    'title': title,
                    'content': content,
                    'messages': messages,
                    'topic_url': f"/topics/{topic['id']}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"基于历史生成内容失败: {e}")
            return None
    
    def _update_conversation_history(self, conversation_id: str, messages: List[Dict[str, Any]]) -> bool:
        """更新对话历史"""
        try:
            return self.conversation_dao.update(conversation_id, {'messages': messages}) > 0
        except Exception as e:
            logger.error(f"更新对话历史失败: {e}")
            return False
    
    def _parse_ai_response_simple(self, content: str) -> dict:
        """
        简化解析逻辑，使用正则表达式直接提取title和content
        """
        import re
        
        try:
            # 打印AI原始回答
            logger.info("="*50)
            logger.info("自动发布 - AI原始回答:")
            logger.info(content)
            logger.info("="*50)
            
            # 更强的正则表达式，处理content中包含双引号的情况
            title_pattern = r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"\s*[,}]'
            content_pattern = r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"'
            
            titles = re.findall(title_pattern, content, re.DOTALL)
            contents = re.findall(content_pattern, content, re.DOTALL)
            
            logger.info(f"自动发布 - 正则提取结果: 找到 {len(titles)} 个title, {len(contents)} 个content")
            logger.info(f"自动发布 - 提取的titles: {titles}")
            logger.info(f"自动发布 - 提取的contents: {[c[:50] + '...' if len(c) > 50 else c for c in contents]}")
            
            # 配对title和content
            valid_items = []
            max_pairs = min(len(titles), len(contents))
            
            for i in range(max_pairs):
                title = titles[i].strip()
                content_text = contents[i].strip()
                
                if title and content_text:
                    # 处理转义字符
                    title = title.replace('\\"', '"').replace('\\n', '\n')
                    content_text = content_text.replace('\\"', '"').replace('\\n', '\n')
                    
                    # 清理content中的方括号内容
                    cleaned_content = re.sub(r'\[[^\]]*\]', '', content_text)
                    valid_items.append({
                        'title': title,
                        'content': cleaned_content
                    })
                    
                    logger.info(f"自动发布 - 处理第{i+1}个对象:")
                    logger.info(f"  原始title: {title}")
                    logger.info(f"  原始content: {content_text[:100]}...")
                    logger.info(f"  清理后content: {cleaned_content[:100]}...")
            
            if valid_items:
                logger.info(f"自动发布 - 最终解析成功: 共{len(valid_items)}个有效对象")
                return {
                    'items': valid_items,
                    'success': True
                }
            
            # 如果没有找到配对，返回原始内容
            logger.warning("自动发布 - 未找到有效的title和content配对，使用原始内容")
            return {
                'items': [{'title': None, 'content': content}],
                'success': False
            }
            
        except Exception as e:
            logger.warning(f"自动发布 - 解析异常: {e}，使用原始内容")
            return {
                'items': [{'title': None, 'content': content}],
                'success': False
            }
    
    def stop_auto_publish_cycle(self, config_id: str) -> bool:
        """停止自动发布循环"""
        try:
            # 停用配置
            rows = self.auto_config_dao.update(config_id, {'is_active': 0})
            
            # 取消该配置的所有待发布任务
            if rows > 0:
                self._cancel_pending_posts(config_id)
                logger.info(f"已停止自动发布循环，配置ID: {config_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"停止自动发布循环失败: {e}")
            return False
    
    def _cancel_pending_posts(self, auto_publish_id: str):
        """取消指定自动发布配置的待发布任务"""
        try:
            sql = """
            DELETE FROM scheduled_posts 
            WHERE auto_publish_id = %s AND status = 'pending'
            """
            self.db.execute_update(sql, (auto_publish_id,))
            logger.info(f"已取消自动发布配置 {auto_publish_id} 的待发布任务")
        except Exception as e:
            logger.error(f"取消待发布任务失败: {e}")

    def _sync_system_prompt(self, messages: List[Dict[str, Any]], current_prompt: str) -> List[Dict[str, Any]]:
        """
        同步历史对话中的system提示词，确保与当前提示词一致

        Args:
            messages: 历史对话消息列表
            current_prompt: 当前的提示词内容

        Returns:
            更新后的消息列表
        """
        try:
            # 查找历史消息中的system消息
            system_message_index = None
            for i, msg in enumerate(messages):
                if msg.get('role') == 'system':
                    system_message_index = i
                    break

            # 如果找到了system消息
            if system_message_index is not None:
                old_prompt = messages[system_message_index].get('content', '')

                # 比较提示词内容是否一致
                if old_prompt != current_prompt:
                    logger.info("检测到提示词不一致，正在同步历史对话...")
                    logger.info(f"旧提示词长度: {len(old_prompt)}")
                    logger.info(f"新提示词长度: {len(current_prompt)}")

                    # 更新system消息的content
                    messages[system_message_index]['content'] = current_prompt

                    logger.info("历史对话中的提示词已更新为当前提示词")
                else:
                    logger.info("历史对话中的提示词已是最新版本，无需更新")
            else:
                logger.info("历史对话中未找到system消息，后续将添加新的system消息")

            return messages

        except Exception as e:
            logger.error(f"同步system提示词失败: {e}")
            # 发生异常时返回原始messages，不影响主流程
            return messages