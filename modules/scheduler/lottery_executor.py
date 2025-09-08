import logging
import requests
import json
from typing import Tuple, Optional
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class LotteryExecutor:
    """抽奖任务执行器 - 处理抽奖数据获取和充值流程"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def execute_lottery_flow(self) -> Tuple[bool, str]:
        """执行完整的抽奖流程：获取抽奖数据 -> 充值"""
        logger.info("开始执行抽奖充值流程")
        
        try:
            lottery_success, lottery_data = self._get_lottery_data()
            if not lottery_success:
                return False, f"获取抽奖数据失败: {lottery_data}"
            
            topup_success, topup_result = self._execute_topup(lottery_data)
            if not topup_success:
                return False, f"充值失败: {topup_result}"
            
            result_msg = f"抽奖充值流程完成 - 抽奖数据: {lottery_data}, 充值结果: {topup_result}"
            logger.info(result_msg)
            return True, result_msg
            
        except Exception as e:
            error_msg = f"抽奖充值流程异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _get_lottery_data(self) -> Tuple[bool, Optional[str]]:
        """获取抽奖数据"""
        url = "https://tw.b4u.qzz.io/luckydraw"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://tw.b4u.qzz.io/",
            "Origin": "https://tw.b4u.qzz.io",
            "Cookie": "token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwia2lkIjoiNmhGVm5JQUpiTTBJUTc1NGpYeE5WUG03YlVNR2tjNF9sMHdKU1c5ODVsb1J2Q3N5dERJTTVUQnFYWTd0MEJ0QWRBSkFTMjhWd3JaNlVVTUZzRWE2SGcifQ..ovFJ5H8vsRKbjzF6cZQ2pg.PqDZfId_DkaAI_TFNbV8fy6L0r_iISULve_QjJWlvoQNmZ9ei-UkQDvLkahVeSy8QKq9AL3zeNkBg2aj47jg7jh41tRjsG1pUwu7r-YXQP6ovMWzkSutBLK8ShtiqqfHK4y1cOglolZXX4UdU6hHLlrRZ1N5_H52jXP3mnCsC1NgDNWOd-2JO1MH5JUvDdaaz2OEDtv77hjFxWLxKIp4aEb1_9QC0mhUBkftxSPROiy0T2iV_VLxoQj93PEIyp7huEB8JODrRvA44nR1NQFApH5DZiXY5sN6IplfU6tdALQVPlSlsPtOD2Rff-jIt2soyOP65ySKnAg3pTQ_UcSHFjx7Y27jZw954Ivxck-0z6fvfMtbv6WJjZKqfsPp2pB-Oj3E-GT3wE6x-KVHhrwSIBRtIBra4sTQGvt1i7XbUD-W2h6d4xQw1cXMUnU5Xjg7npMRBbH1w0Dc_oaLZi4QqJvt7FKOxjfH6PoKzBq545nRfj9CruXnkRQWmZYd07t7AjQ86EgpjgZLVzoATO5fD3MEi7MxvBTOvcY_VrAzRVhEsAXpSRbEzcH3aBKvQC7HuqmrtODsW_fozm_oO7gtYSuk2F9414osqY7O-cGFm54.-fxkBi85R0fRop1eELe1bbTBqusW0ROxx_RlzMcEGxY; HttpOnly; SameSite=Lax; Secure; Path=/; Expires=Wed, 08 Oct 2025 02:33:25 GMT"
        }
        
        data = [{"excludeThankYou": False}]
        
        try:
            response = self.session.post(url=url, headers=headers, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'application/json' in content_type:
                    response_json = response.json()
                    if "data" in response_json:
                        logger.info(f"成功获取抽奖数据: {response_json['data']}")
                        return True, response_json["data"]
                    else:
                        return False, f"响应中没有data字段: {response_json}"
                else:
                    return False, "收到HTML响应，可能需要重新登录或Cookie已过期"
            else:
                return False, f"抽奖请求失败 - 状态码: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, f"抽奖请求超时 (>{self.timeout}秒)"
        except requests.exceptions.RequestException as e:
            return False, f"抽奖请求异常: {str(e)}"
        except json.JSONDecodeError as e:
            return False, f"解析抽奖响应JSON失败: {e}"
    
    def _execute_topup(self, lottery_key: str) -> Tuple[bool, str]:
        """执行充值操作"""
        url = "https://b4u.qzz.io/api/user/topup"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://b4u.qzz.io/",
            "Origin": "https://b4u.qzz.io",
            "Cookie": "session=MTc1NzI5NTg3NHxEWDhFQVFMX2dBQUJFQUVRQUFEX3dQLUFBQVlHYzNSeWFXNW5EQWdBQm5OMFlYUjFjd05wYm5RRUFnQUNCbk4wY21sdVp3d0hBQVZuY285MWNBWnpkSEpwYm1jTUJRQURkbWx3Qm5OMGNtbHVad3dOQUF0dllYVjBhRjl6ZEdGMFpRWnpkSEpwYm1jTURnQU1WelJLZEVKWVVVNTRZa1ZIQm5OMGNtbHVad3dFQUFKcFpBTnBiblFFQkFELUl2QUdjM1J5YVc1bkRBb0FDSFZ6WlhKdVlXMWxCbk4wY21sdVp3d09BQXhzYVc1MWVHUnZYelEwTnpJR2MzUnlhVzVuREFZQUJISnZiR1VEYVc1MEJBSUFBZz09fMUYcKd9VvSsGdfHeZ3QAhaxwpcaPXBAp3_3JKIq52fP"
        }
        
        data = {"key": lottery_key}
        
        try:
            response = self.session.post(url=url, headers=headers, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'application/json' in content_type:
                    response_json = response.json()
                    logger.info(f"充值成功: {response_json}")
                    return True, str(response_json)
                else:
                    logger.info(f"充值完成: {response.text[:200]}")
                    return True, response.text[:200]
            else:
                return False, f"充值请求失败 - 状态码: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, f"充值请求超时 (>{self.timeout}秒)"
        except requests.exceptions.RequestException as e:
            return False, f"充值请求异常: {str(e)}"
    
    def close(self):
        """关闭HTTP会话"""
        if self.session:
            self.session.close()
            logger.info("抽奖执行器HTTP会话已关闭")