import os
import time
import zipfile
import asyncio
import threading
from typing import Dict, Optional

from config import Config
from models import DownloadTask
from downloader.twitter_downloader import TwitterDownloader
import database


class DownloadService:
    """下载服务"""
    
    def __init__(self):
        self._tasks: Dict[str, DownloadTask] = {}
        self._lock = threading.Lock()
        
        # 确保下载目录存在
        os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)
        
        # 初始化数据库
        database.init_db()
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def create_task(self, user_id: str) -> DownloadTask:
        """创建下载任务"""
        task_id = f"{user_id}_{int(time.time())}"
        task = DownloadTask(task_id, user_id)
        
        with self._lock:
            self._tasks[task_id] = task
        
        # 添加到数据库
        database.add_download_history(task_id, user_id)
        
        # 在后台线程中启动下载
        thread = threading.Thread(target=self._run_download, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return task
    
    def _run_download(self, task_id: str):
        """运行下载任务（在后台线程中执行）"""
        task = self.get_task(task_id)
        if not task:
            return
        
        try:
            task.status = 'downloading'
            database.update_download_history(task_id, status='downloading')
            
            # 创建用户下载目录
            user_download_path = os.path.join(Config.DOWNLOAD_FOLDER, task.user_id)
            os.makedirs(user_download_path, exist_ok=True)
            task.download_path = user_download_path
            
            # 进度回调函数
            def progress_callback(progress: int, downloaded_files: int, total_files: int):
                task.progress = progress
                task.downloaded_files = downloaded_files
                task.total_files = total_files
                # 更新数据库
                database.update_download_history(
                    task_id,
                    downloaded_files=downloaded_files,
                    total_files=total_files
                )
            
            # 从数据库获取配置
            proxy = Config.get_proxy()
            cookie = Config.get_cookie()
            
            # 创建下载器
            downloader = TwitterDownloader(
                user_id=task.user_id,
                download_path=user_download_path,
                proxy=proxy,
                cookie=cookie,
                progress_callback=progress_callback
            )
            
            # 创建新的事件循环来运行异步下载
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(downloader.start_download())
                task.total_files = result.get('downloaded_files', 0)
                task.downloaded_files = result.get('downloaded_files', 0)
                task.progress = 100
                
                # 更新数据库
                database.update_download_history(
                    task_id,
                    user_name=result.get('user_name'),
                    total_files=task.total_files,
                    downloaded_files=task.downloaded_files
                )
            finally:
                loop.close()
            
            # 创建ZIP文件
            self._create_zip(task)
            
            task.status = 'completed'
            task.end_time = time.time()
            
            # 更新数据库
            database.update_download_history(
                task_id,
                status='completed',
                zip_path=task.zip_path,
                completed_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.end_time = time.time()
            
            # 更新数据库
            database.update_download_history(
                task_id,
                status='failed',
                error_message=str(e),
                completed_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
    
    def _create_zip(self, task: DownloadTask):
        """创建ZIP压缩文件"""
        zip_filename = f'{task.user_id}_media.zip'
        zip_path = os.path.join(Config.DOWNLOAD_FOLDER, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(task.download_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, task.download_path)
                    zipf.write(file_path, arcname)
        
        task.zip_path = zip_path


# 全局下载服务实例
download_service = DownloadService()