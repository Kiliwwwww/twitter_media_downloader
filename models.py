import time

class DownloadTask:
    """下载任务模型"""
    
    def __init__(self, task_id: str, user_id: str):
        self.task_id = task_id
        self.user_id = user_id
        self.status = 'pending'  # pending, downloading, completed, failed
        self.progress = 0
        self.total_files = 0
        self.downloaded_files = 0
        self.start_time = time.time()
        self.end_time = None
        self.error_message = None
        self.download_path = None
        self.zip_path = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'user_id': self.user_id,
            'status': self.status,
            'progress': self.progress,
            'total_files': self.total_files,
            'downloaded_files': self.downloaded_files,
            'elapsed_time': time.time() - self.start_time,
            'error_message': self.error_message
        }