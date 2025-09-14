#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脉脉Android应用自动化操作脚本
实现指定页面的点击、下滑、返回循环操作
"""

import uiautomator2 as u2
import time
import random
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaimaiAutoBot:
    def __init__(self, device_id=None):
        """初始化自动化机器人"""
        try:
            self.device = u2.connect(device_id)
            self.device.implicitly_wait(10.0)
            logger.info(f"成功连接设备: {self.device.info}")
        except Exception as e:
            logger.error(f"连接设备失败: {e}")
            raise
    
    def start_maimai_app(self):
        """启动脉脉应用"""
        try:
            package_name = "com.taou.maimai"  # 脉脉包名
            self.device.app_start(package_name)
            time.sleep(3)
            logger.info("脉脉应用启动成功")
            return True
        except Exception as e:
            logger.error(f"启动脉脉应用失败: {e}")
            return False
    
    def navigate_to_me_page(self):
        """导航到'我'页面"""
        try:
            # 点击底部导航栏的"我"
            if self.device(text="我").exists(timeout=5):
                self.device(text="我").click()
                time.sleep(2)
                logger.info("成功进入'我'页面")
                return True
            else:
                logger.warning("未找到'我'页面入口")
                return False
        except Exception as e:
            logger.error(f"导航到'我'页面失败: {e}")
            return False
    
    def click_my_content(self):
        """点击'我的内容'"""
        try:
            # 查找并点击"我的内容"
            if self.device(text="我的内容").exists(timeout=5):
                self.device(text="我的内容").click()
                time.sleep(1)
                logger.info("成功点击'我的内容'")
                return True
            else:
                logger.warning("未找到'我的内容'按钮，尝试返回后重试")
                # 按返回键
                self.device.press("back")
                time.sleep(0.5)
                
                # 重新尝试查找"我的内容"
                if self.device(text="我的内容").exists(timeout=5):
                    self.device(text="我的内容").click()
                    time.sleep(0.5)
                    logger.info("重试成功：点击'我的内容'")
                    return True
                else:
                    logger.warning("重试后仍未找到'我的内容'按钮，按home键重新开始")
                    # 按home键回到桌面
                    self.device.press("home")
                    time.sleep(1)
                    # 重新启动脉脉应用
                    self.start_maimai_app()
                    return False
        except Exception as e:
            logger.error(f"点击'我的内容'失败: {e}")
            return False
    
    def scroll_down_for_duration(self, duration_seconds=5):
        """持续下滑指定时间"""
        try:
            logger.info(f"开始持续下滑 {duration_seconds} 秒")
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                # 使用swipe方法替代swipe_ext，避免长按效果
                screen_width = self.device.window_size()[0]
                screen_height = self.device.window_size()[1]
                
                start_x = screen_width // 2
                start_y = screen_height * 0.7  # 起始位置在屏幕70%处
                end_y = screen_height * 0.3    # 结束位置在屏幕30%处
                
                self.device.swipe(start_x, start_y, start_x, end_y, duration=0.05)
                
                
            logger.info(f"完成 {duration_seconds} 秒下滑操作")
            return True
        except Exception as e:
            logger.error(f"持续下滑操作失败: {e}")
            return False
    
    def go_back(self):
        """返回上一页"""
        try:
            self.device.press("back")
            time.sleep(random.uniform(0, 0.1))
            logger.info("执行返回操作")
            return True
        except Exception as e:
            logger.error(f"返回操作失败: {e}")
            return False
    
    def run_infinite_cycle(self):
        """运行无限循环自动化操作"""
        logger.info("开始运行无限循环自动化操作")
        
        # 启动应用
        if not self.start_maimai_app():
            return False
        
        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                logger.info(f"--- 开始第 {cycle_count} 次循环 ---")
                
                # 1. 导航到"我"页面 (仅第一次)
                if cycle_count == 1:
                    if not self.navigate_to_me_page():
                        logger.warning("导航到'我'页面失败，跳过本次循环")
                        continue
                
                # 2. 点击"我的内容"
                result = self.click_my_content()
                if not result:
                    logger.warning("点击'我的内容'失败，重置循环")
                    cycle_count = 0  # 重置循环次数
                    continue
                
                # 3. 持续下拉3秒
                self.scroll_down_for_duration(3)
                
                # 4. 返回
                self.go_back()
                
                # 等待1-3秒再进行下一次循环
                wait_time = random.uniform(0, 0.3)
                logger.info(f"等待 {wait_time:.1f} 秒后进行下一次循环")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            logger.info(f"用户手动停止程序，共完成 {cycle_count} 次循环")
        except Exception as e:
            logger.error(f"循环过程中出错: {e}")
        
        return True

def main():
    """主函数"""
    try:
        # 创建自动化机器人实例
        bot = MaimaiAutoBot()
        
        # 运行无限循环：点击"我" -> 点击"我的内容" -> 下拉5秒 -> 返回 -> 重复
        bot.run_infinite_cycle()
        
    except KeyboardInterrupt:
        logger.info("用户手动停止程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()