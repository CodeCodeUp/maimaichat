import logging
import threading
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import atexit

from modules.scheduled_requests_store_db import ScheduledRequestsStoreDB
from modules.http_request_executor import HttpRequestExecutor

logger = logging.getLogger(__name__)

class DailyRequestScheduler:
    """每日定时HTTP请求调度器"""
    
    def __init__(self, requests_store: ScheduledRequestsStoreDB):
        self.requests_store = requests_store
        self.http_executor = HttpRequestExecutor()
        self.scheduler = None
        self.running = False
        self._lock = threading.Lock()
    
    def start(self):
        """启动定时调度器"""
        with self._lock:
            if self.running:
                logger.warning("每日请求调度器已在运行中")
                return
            
            try:
                # 创建后台调度器
                self.scheduler = BackgroundScheduler(
                    timezone='Asia/Shanghai',  # 设置时区为中国时区
                    job_defaults={
                        'coalesce': False,  # 不合并延迟的任务
                        'max_instances': 1,  # 最多同时运行1个实例
                        'misfire_grace_time': 300  # 错过执行时间5分钟内仍可执行
                    }
                )
                
                # 添加每日9点的定时任务
                self.scheduler.add_job(
                    func=self._execute_daily_requests,
                    trigger=CronTrigger(hour=9, minute=0, second=0),
                    id='daily_http_requests',
                    name='每日9点执行HTTP请求',
                    replace_existing=True
                )
                
                # 添加事件监听器
                self.scheduler.add_listener(
                    self._job_listener, 
                    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
                )
                
                # 启动调度器
                self.scheduler.start()
                self.running = True
                
                # 注册程序退出时的清理函数
                atexit.register(self.stop)
                
                logger.info("每日请求调度器已启动 - 每天9:00执行所有启用的HTTP请求")
                
                # 打印下一次执行时间
                next_run = self.get_next_run_time()
                if next_run:
                    logger.info(f"下次执行时间: {next_run}")
                
            except Exception as e:
                logger.error(f"启动每日请求调度器失败: {e}")
                self.running = False
                raise
    
    def stop(self):
        """停止定时调度器"""
        with self._lock:
            if not self.running:
                return
            
            try:
                if self.scheduler:
                    self.scheduler.shutdown(wait=True)
                    logger.info("每日请求调度器已停止")
                
                if self.http_executor:
                    self.http_executor.close()
                
                self.running = False
                
            except Exception as e:
                logger.error(f"停止每日请求调度器时出错: {e}")
    
    def _execute_daily_requests(self):
        """执行每日的HTTP请求任务"""
        logger.info("开始执行每日定时HTTP请求")
        
        try:
            # 获取所有启用的请求配置
            enabled_requests = self.requests_store.get_enabled_requests()
            
            if not enabled_requests:
                logger.info("没有启用的定时请求配置")
                return
            
            logger.info(f"找到 {len(enabled_requests)} 个启用的请求配置")
            
            success_count = 0
            error_count = 0
            
            # 逐个执行请求
            for i, request_config in enumerate(enabled_requests, 1):
                request_id = request_config['id']
                name = request_config['name']
                url = request_config['url']
                method = request_config['method']
                
                logger.info(f"[{i}/{len(enabled_requests)}] 执行请求: {name}")
                
                try:
                    # 执行HTTP请求
                    success, result = self.http_executor.execute_request(request_config)
                    
                    # 更新执行结果
                    if success:
                        self.requests_store.update_execution_result(
                            request_id, True, result_data=result
                        )
                        success_count += 1
                        logger.info(f"请求成功: {name} - {result}")
                    else:
                        self.requests_store.update_execution_result(
                            request_id, False, error=result
                        )
                        error_count += 1
                        logger.error(f"请求失败: {name} - {result}")
                    
                    # 请求间隔，避免过于频繁
                    if i < len(enabled_requests):
                        time.sleep(1)
                        
                except Exception as e:
                    error_msg = f"执行请求时发生异常: {str(e)}"
                    self.requests_store.update_execution_result(
                        request_id, False, error=error_msg
                    )
                    error_count += 1
                    logger.error(f"请求异常: {name} - {error_msg}")
            
            # 输出执行总结
            total = len(enabled_requests)
            logger.info(f"每日定时请求执行完成 - 总计: {total}, 成功: {success_count}, 失败: {error_count}")
            
        except Exception as e:
            logger.error(f"执行每日定时请求时发生异常: {e}")
    
    def _job_listener(self, event):
        """任务执行事件监听器"""
        job_id = event.job_id
        
        if event.exception:
            logger.error(f"定时任务 {job_id} 执行失败: {event.exception}")
        else:
            logger.info(f"定时任务 {job_id} 执行完成")
    
    def get_next_run_time(self):
        """获取下次执行时间"""
        if not self.scheduler:
            return None
        
        job = self.scheduler.get_job('daily_http_requests')
        if job:
            return job.next_run_time
        return None
    
    def get_status(self):
        """获取调度器状态"""
        next_run = self.get_next_run_time()
        enabled_count = self.requests_store.get_enabled_count()
        
        return {
            'running': self.running,
            'next_run_time': next_run.isoformat() if next_run else None,
            'enabled_requests_count': enabled_count,
            'scheduler_state': self.scheduler.state if self.scheduler else None
        }
    
    def trigger_manual_execution(self):
        """手动触发执行（用于测试）"""
        logger.info("手动触发每日定时请求执行")
        try:
            # 在新线程中执行，避免阻塞
            thread = threading.Thread(
                target=self._execute_daily_requests,
                name='ManualExecution'
            )
            thread.start()
            return True, "手动执行已启动"
        except Exception as e:
            error_msg = f"手动执行失败: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def add_test_execution(self, delay_seconds=5):
        """添加测试执行任务（delay_seconds秒后执行）"""
        if not self.scheduler:
            return False, "调度器未启动"
        
        try:
            from datetime import datetime, timedelta
            
            run_time = datetime.now() + timedelta(seconds=delay_seconds)
            
            self.scheduler.add_job(
                func=self._execute_daily_requests,
                trigger='date',
                run_date=run_time,
                id=f'test_execution_{int(time.time())}',
                name=f'测试执行任务 - {delay_seconds}秒后',
                replace_existing=True
            )
            
            logger.info(f"已添加测试执行任务，将在 {run_time.strftime('%H:%M:%S')} 执行")
            return True, f"测试任务将在{delay_seconds}秒后执行"
        except Exception as e:
            error_msg = f"添加测试任务失败: {e}"
            logger.error(error_msg)
            return False, error_msg