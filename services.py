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
        """获取任务（优先内存，其次数据库）"""
        # 先从内存获取
        task = self._tasks.get(task_id)
        if task:
            return task
        
        # 内存中没有，从数据库获取
        history = database.get_download_by_task_id(task_id)
        if history:
            task = DownloadTask(task_id, history['user_id'])
            task.status = history['status']
            task.total_files = history.get('total_files', 0)
            task.downloaded_files = history.get('downloaded_files', 0)
            task.zip_path = history.get('zip_path')
            task.error_message = history.get('error_message')
            task.progress = 100 if history['status'] == 'completed' else 0
            return task
        
        return None
    
    def create_task(self, user_id: str, download_type: str = 'all') -> DownloadTask:
        """创建下载任务"""
        task_id = f"{user_id}_{int(time.time())}"
        task = DownloadTask(task_id, user_id, download_type)
        
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
    
    def clear_all_cache(self) -> dict:
        """清理所有缓存文件和下载历史"""
        import shutil
        
        deleted_files = 0
        deleted_dirs = 0
        
        download_folder = Config.DOWNLOAD_FOLDER
        
        if os.path.exists(download_folder):
            try:
                # 遍历下载目录
                for item in os.listdir(download_folder):
                    item_path = os.path.join(download_folder, item)
                    
                    # 跳过隐藏文件
                    if item.startswith('.'):
                        continue
                    
                    if os.path.isfile(item_path):
                        # 删除文件（ZIP文件等）
                        os.remove(item_path)
                        deleted_files += 1
                    elif os.path.isdir(item_path):
                        # 删除用户下载目录
                        file_count = sum(len(files) for _, _, files in os.walk(item_path))
                        shutil.rmtree(item_path)
                        deleted_dirs += 1
                        deleted_files += file_count
            except Exception as e:
                raise Exception(f'清理缓存失败: {str(e)}')
        
        # 清空下载历史
        database.clear_all_download_history()
        
        return {'deleted_files': deleted_files, 'deleted_dirs': deleted_dirs}
    
    def _create_zip(self, task: DownloadTask):
        """创建ZIP压缩文件，按文件类型分类"""
        # 文件类型分类
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.gif'}
        image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        
        def get_file_type(filename: str) -> str:
            """根据文件扩展名返回文件类型"""
            ext = os.path.splitext(filename)[1].lower()
            if ext in video_exts:
                return 'video'
            elif ext in image_exts:
                return 'image'
            else:
                return 'other'
        
        def get_category(filename: str) -> str:
            """根据文件扩展名返回分类文件夹名"""
            file_type = get_file_type(filename)
            if file_type == 'video':
                return 'videos'
            elif file_type == 'image':
                return 'images'
            else:
                return 'others'
        
        # 生成时间戳
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # 根据下载类型生成文件名
        download_type = task.download_type
        if download_type == 'video':
            zip_filename = f'{task.user_id}_video_{timestamp}.zip'
        elif download_type == 'image':
            zip_filename = f'{task.user_id}_img_{timestamp}.zip'
        else:  # all
            zip_filename = f'{task.user_id}_video_img_{timestamp}.zip'
        
        zip_path = os.path.join(Config.DOWNLOAD_FOLDER, zip_filename)
        
        # 获取用户信息用于文件夹名称
        from database import get_download_by_task_id
        history = get_download_by_task_id(task.task_id)
        user_name = history.get('user_name') if history else None
        # 构建根目录名称：用户名_用户ID
        folder_name = f'{user_name}_{task.user_id}' if user_name else task.user_id
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(task.download_path):
                for file in files:
                    file_type = get_file_type(file)
                    
                    # 根据下载类型过滤文件
                    if download_type == 'video' and file_type != 'video':
                        continue
                    if download_type == 'image' and file_type != 'image':
                        continue
                    
                    file_path = os.path.join(root, file)
                    # 获取分类文件夹
                    category = get_category(file)
                    # 构建ZIP内的路径：根目录/分类文件夹/原文件名
                    arcname = f'{folder_name}/{category}/{file}'
                    zipf.write(file_path, arcname)
        
        task.zip_path = zip_path


# 全局下载服务实例
download_service = DownloadService()