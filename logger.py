import os
import logging
from datetime import datetime
from typing import Optional


class DownloadLogger:
    """下载任务日志管理器"""
    
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    
    def __init__(self, task_id: str, user_id: str):
        self.task_id = task_id
        self.user_id = user_id
        self.logger = None
        self.log_file = None
        self._setup_logger()
    
    def _setup_logger(self):
        """初始化日志器"""
        # 确保日志目录存在
        os.makedirs(self.LOG_DIR, exist_ok=True)
        
        # 创建日志文件名：task_id_日期.log
        date_str = datetime.now().strftime('%Y%m%d')
        log_filename = f'{self.task_id}_{date_str}.log'
        self.log_file = os.path.join(self.LOG_DIR, log_filename)
        
        # 创建logger
        self.logger = logging.getLogger(f'download_{self.task_id}')
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 文件handler
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 格式
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
        
        self.info(f'=== 下载任务开始 ===')
        self.info(f'任务ID: {self.task_id}')
        self.info(f'用户ID: {self.user_id}')
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def log_download_success(self, filename: str, file_size: int = 0):
        """记录下载成功"""
        size_str = self._format_size(file_size) if file_size > 0 else 'unknown'
        self.info(f'[下载成功] {filename} ({size_str})')
    
    def log_download_skip(self, filename: str):
        """记录跳过已存在文件"""
        self.info(f'[跳过] 文件已存在: {filename}')
    
    def log_download_failed(self, filename: str, error: str, retry_count: int):
        """记录下载失败"""
        self.error(f'[下载失败] {filename} - 错误: {error} (重试次数: {retry_count})')
    
    def log_retry(self, filename: str, retry_count: int, max_retries: int):
        """记录重试"""
        self.warning(f'[重试] {filename} - 第{retry_count}/{max_retries}次重试')
    
    def log_progress(self, downloaded: int, total: int, skipped: int = 0):
        """记录进度"""
        self.info(f'[进度] 已下载: {downloaded}, 已跳过: {skipped}, 总计: {total}')
    
    def log_task_complete(self, downloaded: int, failed: int, skipped: int, total_time: float):
        """记录任务完成"""
        self.info(f'=== 下载任务完成 ===')
        self.info(f'成功下载: {downloaded} 个文件')
        self.info(f'下载失败: {failed} 个文件')
        self.info(f'跳过文件: {skipped} 个文件')
        self.info(f'总耗时: {total_time:.2f} 秒')
    
    def log_task_failed(self, error: str, total_time: float):
        """记录任务失败"""
        self.error(f'=== 下载任务失败 ===')
        self.error(f'错误信息: {error}')
        self.error(f'总耗时: {total_time:.2f} 秒')
    
    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.2f} {unit}'
            size /= 1024
        return f'{size:.2f} TB'
    
    @staticmethod
    def get_log_content(task_id: str) -> Optional[str]:
        """获取任务日志内容"""
        log_dir = DownloadLogger.LOG_DIR
        if not os.path.exists(log_dir):
            return None
        
        # 查找匹配的日志文件
        for filename in os.listdir(log_dir):
            if filename.startswith(task_id) and filename.endswith('.log'):
                log_path = os.path.join(log_dir, filename)
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception:
                    return None
        return None
    
    @staticmethod
    def get_all_logs() -> list:
        """获取所有日志文件列表"""
        log_dir = DownloadLogger.LOG_DIR
        if not os.path.exists(log_dir):
            return []
        
        logs = []
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                log_path = os.path.join(log_dir, filename)
                stat = os.stat(log_path)
                logs.append({
                    'filename': filename,
                    'task_id': filename.rsplit('_', 1)[0] if '_' in filename else filename,
                    'size': stat.st_size,
                    'modified_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # 按修改时间倒序
        logs.sort(key=lambda x: x['modified_at'], reverse=True)
        return logs
    
    @staticmethod
    def delete_log(task_id: str) -> bool:
        """删除任务日志"""
        log_dir = DownloadLogger.LOG_DIR
        if not os.path.exists(log_dir):
            return False
        
        for filename in os.listdir(log_dir):
            if filename.startswith(task_id) and filename.endswith('.log'):
                log_path = os.path.join(log_dir, filename)
                try:
                    os.remove(log_path)
                    return True
                except Exception:
                    return False
        return False
    
    @staticmethod
    def clear_all_logs() -> int:
        """清空所有日志"""
        log_dir = DownloadLogger.LOG_DIR
        if not os.path.exists(log_dir):
            return 0
        
        count = 0
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                log_path = os.path.join(log_dir, filename)
                try:
                    os.remove(log_path)
                    count += 1
                except Exception:
                    pass
        return count
