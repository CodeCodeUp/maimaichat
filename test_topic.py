#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试话题URL解析功能
"""
import sys
sys.path.append('.')

from modules.maimai_api import MaimaiAPI
from config import Config

def test_topic_extraction():
    """测试话题ID提取功能"""
    
    api = MaimaiAPI(Config.MAIMAI_CONFIG)
    
    # 测试简单URL格式
    simple_url = "https://maimai.cn/n/content/global-topic?circle_type=9&topic_id=zGMekSRN"
    topic_id = api.extract_topic_id(simple_url)
    print(f"简单URL格式测试:")
    print(f"URL: {simple_url}")
    print(f"提取的topic_id: {topic_id}")
    
    # 测试复杂URL格式  
    complex_url = 'https://api.taou.com/sdk/publish?topics=%5B%7B%22tag_id%22%3A0%2C%22id%22%3A%22kGhbfHKZ%22%2C%22name%22%3A%22%E6%88%BF%E4%BB%B7%E4%B8%8B%E8%B7%8C%E5%88%B0%E4%BB%80%E4%B9%88%E7%A8%8B%E5%BA%A6%E5%8F%AF%E4%BB%A5%E6%8A%84%E5%BA%95%22%7D%5D'
    topic_id2 = api.extract_topic_id(complex_url)
    print(f"\n复杂URL格式测试:")
    print(f"URL: {complex_url[:80]}...")
    print(f"提取的topic_id: {topic_id2}")
    
    # 测试带话题的发布（模拟）
    print(f"\n测试话题发布功能（仅构建参数，不实际发布）:")
    
    # 模拟发布准备过程
    test_content = "测试带话题的内容发布"
    result = api.publish_content(
        title="话题测试",
        content=test_content,
        topic_url=simple_url
    )
    
    print(f"发布结果: {result.get('success')}")
    if result.get('success'):
        print(f"帖子ID: {result.get('data', {}).get('gossip', {}).get('id')}")
    else:
        print(f"错误: {result.get('error')}")

if __name__ == "__main__":
    test_topic_extraction()