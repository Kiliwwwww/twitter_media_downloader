import os
import json
import asyncio
import threading
import time
import zipfile
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
import httpx
from downloader.twitter_downloader import TwitterDownloader

app = Flask(__name__)

# 配置
app.config['DOWNLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 确保下载目录存在
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# 存储下载任务状态
download_tasks = {}

class DownloadTask:
    def __init__(self, task_id, user_id):
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

def create_app():
    return app

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.get_json()
    user_id = data.get('user_id', '').strip()
    
    if not user_id:
        return jsonify({'error': '请输入用户ID'}), 400
    
    # 生成任务ID
    task_id = f"{user_id}_{int(time.time())}"
    
    # 创建下载任务
    task = DownloadTask(task_id, user_id)
    download_tasks[task_id] = task
    
    # 在后台线程中启动下载
    thread = threading.Thread(target=run_download_task, args=(task_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'message': f'开始下载用户 {user_id} 的媒体文件'
    })

@app.route('/api/progress/<task_id>')
def get_progress(task_id):
    task = download_tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify({
        'task_id': task.task_id,
        'user_id': task.user_id,
        'status': task.status,
        'progress': task.progress,
        'total_files': task.total_files,
        'downloaded_files': task.downloaded_files,
        'elapsed_time': time.time() - task.start_time,
        'error_message': task.error_message
    })

@app.route('/api/download/<task_id>')
def download_file(task_id):
    task = download_tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    if task.status != 'completed':
        return jsonify({'error': '下载尚未完成'}), 400
    
    if not task.zip_path or not os.path.exists(task.zip_path):
        return jsonify({'error': '压缩文件不存在'}), 404
    
    return send_file(
        task.zip_path,
        as_attachment=True,
        download_name=f'{task.user_id}_media.zip'
    )

def run_download_task(task_id):
    """在后台线程中运行下载任务"""
    task = download_tasks.get(task_id)
    if not task:
        return
    
    try:
        task.status = 'downloading'
        
        # 创建用户下载目录
        user_download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], task.user_id)
        os.makedirs(user_download_path, exist_ok=True)
        task.download_path = user_download_path
        
        # 进度回调函数
        def progress_callback(progress, downloaded_files, total_files):
            task.progress = progress
            task.downloaded_files = downloaded_files
            task.total_files = total_files
        
        # 创建下载器
        downloader = TwitterDownloader(
            user_id=task.user_id,
            download_path=user_download_path,
            proxy="http://127.0.0.1:7890",
            cookie="auth_token=57e0355a3d8af03456b2363bc2e2414bd196ec3d; ct0=c5b52759848ec617418a1f8efd3ed113ceac195f8f6d4007bce0385b0b3f6abd342a12c9e77a4532ed056fb637d982328f96f2d2058b35214eff48b1806d9e151f266998a83a99a8e2a89554e9141aca",
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
        finally:
            loop.close()
        
        # 创建ZIP文件
        create_zip_file(task)
        
        task.status = 'completed'
        task.end_time = time.time()
        
    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.end_time = time.time()

def create_zip_file(task):
    """创建ZIP压缩文件"""
    zip_filename = f'{task.user_id}_media.zip'
    zip_path = os.path.join(app.config['DOWNLOAD_FOLDER'], zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(task.download_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, task.download_path)
                zipf.write(file_path, arcname)
    
    task.zip_path = zip_path

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)