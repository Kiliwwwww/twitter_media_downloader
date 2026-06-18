import os
import glob
import zipfile
import asyncio
import re
import json
import time
import queue
import httpx
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, g, Response, after_this_request

from config import Config
from services import download_service
from realtime_logger import log_manager
import database
from auth import login_required, get_current_user, admin_required

# 媒体文件扩展名
MEDIA_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm', '.webp'}


def count_media_files(user_id: str) -> int:
    """统计用户文件夹中的实际媒体文件数量"""
    user_folder = os.path.join(Config.DOWNLOAD_FOLDER, user_id)
    if not os.path.isdir(user_folder):
        return 0
    
    count = 0
    for ext in MEDIA_EXTENSIONS:
        count += len(glob.glob(os.path.join(user_folder, f'*{ext}')))
    return count


def get_folder_size(user_id: str) -> int:
    """获取用户文件夹的实际总大小"""
    user_folder = os.path.join(Config.DOWNLOAD_FOLDER, user_id)
    if not os.path.isdir(user_folder):
        return 0
    
    total_size = 0
    for ext in MEDIA_EXTENSIONS:
        for f in glob.glob(os.path.join(user_folder, f'*{ext}')):
            if os.path.isfile(f):
                total_size += os.path.getsize(f)
    return total_size

# 创建蓝图
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    """首页"""
    return render_template('index.html')


@main_bp.route('/config')
@login_required
def config_page():
    """配置管理页面"""
    return render_template('config.html')


@main_bp.route('/history')
@login_required
def history_page():
    """下载历史页面"""
    return render_template('history.html')


@main_bp.route('/detail/<user_id>')
@login_required
def detail_page(user_id: str):
    """用户媒体详情页面"""
    return render_template('detail.html', user_id=user_id)


@main_bp.route('/gallery')
@login_required
def gallery_page():
    """用户画廊页面"""
    return render_template('gallery.html')


@main_bp.route('/api/download', methods=['POST'])
@login_required
def start_download():
    """开始下载"""
    data = request.get_json()
    user_ids = data.get('user_id', '').strip()
    download_type = data.get('download_type', 'all')  # all, video, image
    export_xlsx = data.get('export_xlsx', False)  # 是否导出xlsx
    create_zip = data.get('create_zip', False)  # 是否生成压缩包
    
    if not user_ids:
        return jsonify({'error': '请输入用户ID'}), 400
    
    if download_type not in ['all', 'video', 'image']:
        return jsonify({'error': '无效的下载类型'}), 400
    
    # 支持多个用户ID，用逗号分隔
    user_id_list = [uid.strip() for uid in user_ids.split(',') if uid.strip()]
    
    if not user_id_list:
        return jsonify({'error': '请输入有效的用户ID'}), 400
    
    # 获取当前登录用户ID
    current_user = get_current_user()
    account_user_id = current_user['id'] if current_user else None
    
    # 创建下载任务
    tasks = []
    for user_id in user_id_list:
        task = download_service.create_task(user_id, download_type, account_user_id, export_xlsx=export_xlsx, create_zip=create_zip)
        tasks.append({
            'task_id': task.task_id,
            'user_id': user_id
        })
    
    if len(tasks) == 1:
        return jsonify({
            'task_id': tasks[0]['task_id'],
            'message': f'开始下载用户 {tasks[0]["user_id"]} 的媒体文件'
        })
    else:
        return jsonify({
            'tasks': tasks,
            'message': f'已创建 {len(tasks)} 个下载任务'
        })


@main_bp.route('/api/progress/<task_id>')
def get_progress(task_id: str):
    """获取下载进度"""
    task = download_service.get_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(task.to_dict())


@main_bp.route('/api/download/<task_id>')
def download_file(task_id: str):
    """下载文件"""
    task = download_service.get_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    if task.status != 'completed':
        return jsonify({'error': '下载尚未完成'}), 400
    
    if not task.zip_path or not os.path.exists(task.zip_path):
        return jsonify({'error': '压缩文件不存在'}), 404
    
    # 从 zip_path 获取文件名
    download_name = os.path.basename(task.zip_path)
    
    return send_file(
        task.zip_path,
        as_attachment=True,
        download_name=download_name
    )


@main_bp.route('/api/zip/<user_id>', methods=['POST'])
@login_required
def create_user_zip(user_id: str):
    """为指定用户创建ZIP压缩包"""
    try:
        user_dir = os.path.join(Config.DOWNLOAD_FOLDER, user_id)
        
        if not os.path.exists(user_dir) or not os.path.isdir(user_dir):
            return jsonify({'error': '用户文件夹不存在'}), 404
        
        # 检查是否有媒体文件
        media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.avi', '.mkv', '.webm'}
        has_media = False
        for filename in os.listdir(user_dir):
            ext = os.path.splitext(filename)[1].lower()
            if ext in media_extensions:
                has_media = True
                break
        
        if not has_media:
            return jsonify({'error': '用户文件夹中没有媒体文件'}), 400
        
        # 获取用户信息
        history = database.get_latest_download_by_user_id(user_id)
        user_name = history.get('user_name') if history else None
        
        # 生成ZIP文件名
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        name_prefix = f'{user_name}_{user_id}' if user_name else user_id
        zip_filename = f'{name_prefix}_video_img_{timestamp}.zip'
        zip_path = os.path.join(Config.DOWNLOAD_FOLDER, zip_filename)
        
        # 创建ZIP文件
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.gif'}
        image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in os.listdir(user_dir):
                filepath = os.path.join(user_dir, filename)
                if not os.path.isfile(filepath):
                    continue
                
                ext = os.path.splitext(filename)[1].lower()
                if ext not in media_extensions:
                    continue
                
                # 分类到子文件夹
                if ext in video_exts:
                    arcname = f'{name_prefix}/videos/{filename}'
                elif ext in image_exts:
                    arcname = f'{name_prefix}/images/{filename}'
                else:
                    arcname = f'{name_prefix}/others/{filename}'
                
                zipf.write(filepath, arcname)
        
        # 返回下载链接
        return jsonify({
            'message': 'ZIP文件创建成功',
            'zip_filename': zip_filename,
            'download_url': f'/api/download-zip/{zip_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': f'创建ZIP文件失败: {str(e)}'}), 500


@main_bp.route('/api/download-zip/<filename>')
@login_required
def download_zip(filename: str):
    """下载ZIP文件"""
    import threading
    
    zip_path = os.path.join(Config.DOWNLOAD_FOLDER, filename)
    
    if not os.path.exists(zip_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 获取删除延迟时间配置（默认20分钟）
    current_user = get_current_user()
    account_user_id = current_user['id'] if current_user else None
    delete_delay = database.get_config('zip_delete_delay', account_user_id)
    delete_minutes = int(delete_delay) if delete_delay else 20
    
    # 定时删除ZIP文件
    def delete_zip_later():
        import time
        time.sleep(delete_minutes * 60)
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
                print(f'已删除ZIP文件: {filename}')
        except Exception as e:
            print(f'删除ZIP文件失败: {e}')
    
    thread = threading.Thread(target=delete_zip_later)
    thread.daemon = True
    thread.start()
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=filename
    )


# 配置管理API
@main_bp.route('/api/configs')
@login_required
def get_configs():
    """获取当前用户的配置"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '未登录'}), 401
    
    configs = database.get_all_configs(user_id=current_user['id'])
    # 过滤掉系统配置项
    configs = [c for c in configs if c['key'] != 'secret_key']
    return jsonify(configs)


@main_bp.route('/api/configs', methods=['PUT'])
@login_required
def update_configs():
    """更新当前用户的配置"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的数据'}), 400
    
    try:
        for key, value in data.items():
            database.update_config(key, value, user_id=current_user['id'])
        return jsonify({'message': '配置已更新'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 下载历史API
@main_bp.route('/api/history')
@login_required
def get_history():
    """获取下载历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    date = request.args.get('date', '').strip()
    
    offset = (page - 1) * per_page
    
    # 获取当前用户信息，用于数据隔离
    current_user = get_current_user()
    account_user_id = None
    if current_user and current_user['role'] != 'admin':
        # 普通用户只能看到自己的记录
        account_user_id = current_user['id']
    
    history = database.get_download_history(
        limit=per_page, 
        offset=offset,
        keyword=keyword,
        status=status,
        date=date,
        account_user_id=account_user_id
    )
    total = database.get_download_history_count(
        keyword=keyword,
        status=status,
        date=date,
        account_user_id=account_user_id
    )
    
    # 检查本地是否存在ZIP文件，如果不存在则清空zip_path
    for item in history:
        if item.get('zip_path') and not os.path.exists(item['zip_path']):
            item['zip_path'] = None
    
    return jsonify({
        'data': history,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@main_bp.route('/api/history/<task_id>', methods=['DELETE'])
def delete_history(task_id: str):
    """删除下载历史"""
    try:
        import shutil
        
        # 先获取下载记录，获取用户ID
        history = database.get_download_by_task_id(task_id)
        if history and history.get('user_id'):
            user_id = history['user_id']
            user_dir = os.path.join(Config.DOWNLOAD_FOLDER, user_id)
            
            # 检查是否还有其他下载记录使用同一个用户目录
            other_records = database.get_download_history_by_user_id(user_id)
            # 排除当前要删除的记录
            other_records = [r for r in other_records if r['task_id'] != task_id]
            
            # 如果没有其他记录使用这个用户目录，则删除
            if not other_records and os.path.exists(user_dir):
                shutil.rmtree(user_dir)
        
        database.delete_download_history(task_id)
        return jsonify({'message': '已删除'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 用户画廊API
@main_bp.route('/api/gallery/users')
@login_required
def get_gallery_users():
    """获取画廊用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()

    offset = (page - 1) * per_page

    current_user = get_current_user()
    account_user_id = None
    if current_user and current_user['role'] != 'admin':
        account_user_id = current_user['id']

    users = database.get_gallery_users(
        keyword=keyword,
        limit=per_page,
        offset=offset,
        account_user_id=account_user_id
    )
    total = database.get_gallery_users_count(
        keyword=keyword,
        account_user_id=account_user_id
    )

    # 使用文件夹中的实际媒体文件数量和大小替代数据库统计
    for user in users:
        user['total_files'] = count_media_files(user['user_id'])
        user['total_size'] = get_folder_size(user['user_id'])

    return jsonify({
        'data': users,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@main_bp.route('/api/cache', methods=['DELETE'])
def clear_cache():
    """清理所有缓存文件"""
    try:
        result = download_service.clear_all_cache()
        return jsonify({
            'message': f'已清理 {result["deleted_files"]} 个文件和 {result["deleted_dirs"]} 个目录',
            'deleted_files': result['deleted_files'],
            'deleted_dirs': result['deleted_dirs']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


async def _fetch_user_avatar(user_id: str, account_user_id: int = None) -> str:
    """异步获取用户头像URL"""
    proxy = Config.get_proxy(user_id=account_user_id)
    cookie = Config.get_cookie(user_id=account_user_id)
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'cookie': cookie
    }
    
    re_token = r'ct0=([a-f0-9]+)'
    match = re.search(re_token, cookie)
    if match:
        headers['x-csrf-token'] = match.group(1)
    
    headers['referer'] = f'https://twitter.com/{user_id}'
    
    url = f'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName?variables={{"screen_name":"{user_id}","withSafetyModeUserFields":false}}&features={{"hidden_profile_likes_enabled":false,"hidden_profile_subscriptions_enabled":false,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}}&fieldToggles={{"withAuxiliaryUserLabels":false}}'
    
    _proxy = proxy if proxy and proxy.strip() else None
    
    async with httpx.AsyncClient(proxy=_proxy) as client:
        response = await client.get(url.replace('{', '%7B').replace('}', '%7D'), headers=headers, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                user_result = data['data']['user']['result']
                avatar_url = user_result.get('legacy', {}).get('profile_image_url_https')
                # 将头像URL替换为高清版本 _400x400
                if avatar_url:
                    avatar_url = avatar_url.replace('_normal', '_400x400')
                return avatar_url
    return None


async def _download_avatar(url: str, save_path: str, account_user_id: int = None) -> bool:
    """下载头像并保存到本地"""
    try:
        proxy = Config.get_proxy(user_id=account_user_id)
        _proxy = proxy if proxy and proxy.strip() else None
        
        async with httpx.AsyncClient(proxy=_proxy) as client:
            response = await client.get(url, timeout=15.0)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
    except Exception:
        pass
    return False


@main_bp.route('/api/avatar/<user_id>')
@login_required
def get_user_avatar(user_id: str):
    """获取用户头像并保存到本地"""
    try:
        current_user = get_current_user()
        account_user_id = current_user['id'] if current_user else None
        
        # 检查本地是否已有头像
        avatar_dir = os.path.join(Config.BASE_DIR, 'downloads', '.avatars')
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            local_path = os.path.join(avatar_dir, f'{user_id}{ext}')
            if os.path.exists(local_path):
                return jsonify({'avatar_url': f'/api/avatar-file/{user_id}'})
        
        # 从 Twitter 获取头像 URL
        loop = asyncio.new_event_loop()
        avatar_url = loop.run_until_complete(_fetch_user_avatar(user_id, account_user_id=account_user_id))
        loop.close()
        
        if avatar_url:
            # 下载并保存到本地
            ext = '.jpg'
            if '.png' in avatar_url:
                ext = '.png'
            elif '.webp' in avatar_url:
                ext = '.webp'
            
            save_path = os.path.join(avatar_dir, f'{user_id}{ext}')
            loop = asyncio.new_event_loop()
            success = loop.run_until_complete(_download_avatar(avatar_url, save_path, account_user_id))
            loop.close()
            
            if success:
                local_url = f'/api/avatar-file/{user_id}'
                database.update_avatar_by_user_id(user_id, local_url)
                return jsonify({'avatar_url': local_url})
        
        return jsonify({'avatar_url': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/avatar-file/<user_id>')
@login_required
def serve_avatar_file(user_id: str):
    """提供本地头像文件访问"""
    try:
        avatar_dir = os.path.join(Config.BASE_DIR, 'downloads', '.avatars')
        
        # 查找头像文件
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            file_path = os.path.join(avatar_dir, f'{user_id}{ext}')
            if os.path.exists(file_path):
                return send_file(file_path)
        
        return jsonify({'error': '头像不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 用户媒体详情API ====================

def _generate_video_thumbnail(video_path: str, thumb_path: str) -> bool:
    """使用ffmpeg生成视频缩略图"""
    try:
        import subprocess
        # 确保缩略图目录存在
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        # 使用ffmpeg提取第1秒的帧作为缩略图
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-vf', 'scale=320:-1',
            '-y',
            thumb_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0 and os.path.exists(thumb_path)
    except Exception:
        return False


@main_bp.route('/api/user-media/<user_id>')
@login_required
def get_user_media(user_id: str):
    """获取指定用户的本地媒体文件列表"""
    try:
        from config import Config
        
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 24, type=int)
        file_type = request.args.get('type', 'all').strip()  # all, image, video
        
        # 构建用户目录路径
        user_dir = os.path.join(Config.BASE_DIR, 'downloads', user_id)
        thumb_dir = os.path.join(Config.BASE_DIR, 'downloads', '.thumbnails', user_id)
        
        if not os.path.exists(user_dir):
            return jsonify({
                'user_id': user_id,
                'files': [],
                'total': 0,
                'images': 0,
                'videos': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            })
        
        # 获取所有媒体文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        
        all_files = []
        image_count = 0
        video_count = 0
        
        for filename in os.listdir(user_dir):
            filepath = os.path.join(user_dir, filename)
            if not os.path.isfile(filepath):
                continue
            
            ext = os.path.splitext(filename)[1].lower()
            file_type_detected = None
            
            if ext in image_extensions:
                file_type_detected = 'image'
                image_count += 1
            elif ext in video_extensions:
                file_type_detected = 'video'
                video_count += 1
            else:
                continue
            
            # 获取文件信息
            stat = os.stat(filepath)
            
            # 从文件名解析日期 (格式: YYYY-MM-DD HH-MM-type_id.ext)
            date_str = ''
            parts = filename.split(' ')
            if len(parts) >= 2:
                date_str = parts[0] + ' ' + parts[1].split('-')[0] + ':' + parts[1].split('-')[1] if len(parts[1].split('-')) >= 2 else ''
            
            file_info = {
                'name': filename,
                'path': f'/api/media-file/{user_id}/{filename}',
                'type': file_type_detected,
                'size': stat.st_size,
                'date': date_str,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'thumb': None
            }
            
            all_files.append(file_info)
        
        # 按文件名倒序排列（文件名包含日期，最新的在前）
        all_files.sort(key=lambda x: x['name'], reverse=True)
        
        # 按类型筛选
        if file_type == 'image':
            filtered_files = [f for f in all_files if f['type'] == 'image']
        elif file_type == 'video':
            filtered_files = [f for f in all_files if f['type'] == 'video']
        else:
            filtered_files = all_files
        
        total = len(filtered_files)
        total_pages = (total + per_page - 1) // per_page
        
        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        page_files = filtered_files[start:end]
        
        # 只为当前页的视频生成缩略图
        for file_info in page_files:
            if file_info['type'] == 'video':
                thumb_filename = os.path.splitext(file_info['name'])[0] + '.jpg'
                thumb_path = os.path.join(thumb_dir, thumb_filename)
                filepath = os.path.join(user_dir, file_info['name'])
                
                # 如果缩略图不存在则生成
                if not os.path.exists(thumb_path):
                    _generate_video_thumbnail(filepath, thumb_path)
                
                if os.path.exists(thumb_path):
                    file_info['thumb'] = f'/api/thumbnail/{user_id}/{thumb_filename}'
        
        return jsonify({
            'user_id': user_id,
            'files': page_files,
            'total': total,
            'images': image_count,
            'videos': video_count,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/thumbnail/<user_id>/<filename>')
@login_required
def serve_thumbnail(user_id: str, filename: str):
    """提供缩略图访问"""
    try:
        from config import Config
        
        thumb_path = os.path.join(Config.BASE_DIR, 'downloads', '.thumbnails', user_id, filename)
        
        if not os.path.exists(thumb_path):
            return jsonify({'error': '缩略图不存在'}), 404
        
        return send_file(thumb_path, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/media-file/<user_id>/<filename>')
@login_required
def serve_media_file(user_id: str, filename: str):
    """提供媒体文件访问"""
    try:
        from config import Config
        
        filepath = os.path.join(Config.BASE_DIR, 'downloads', user_id, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(filepath)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 实时日志SSE接口 ====================

@main_bp.route('/api/logs/stream')
@admin_required
def stream_all_logs():
    """SSE: 实时推送所有日志"""
    def generate():
        q = log_manager.subscribe_all()
        try:
            # 先发送已有日志
            existing = log_manager.get_all_logs(limit=50)
            for log in reversed(existing):
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
            
            # 实时推送新日志
            while True:
                try:
                    entry = q.get(timeout=30)
                    yield f"data: {json.dumps(entry.to_dict(), ensure_ascii=False)}\n\n"
                except queue.Empty:
                    # 发送心跳保持连接
                    yield f": heartbeat\n\n"
        except GeneratorExit:
            pass
        finally:
            log_manager.unsubscribe_all(q)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@main_bp.route('/api/logs/stream/<task_id>')
@login_required
def stream_task_logs(task_id: str):
    """SSE: 实时推送指定任务日志"""
    def generate():
        q = log_manager.subscribe_task(task_id)
        try:
            # 先发送已有日志
            existing = log_manager.get_logs(task_id)
            for log in existing:
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
            
            # 实时推送新日志
            while True:
                try:
                    entry = q.get(timeout=30)
                    yield f"data: {json.dumps(entry.to_dict(), ensure_ascii=False)}\n\n"
                except queue.Empty:
                    yield f": heartbeat\n\n"
        except GeneratorExit:
            pass
        finally:
            log_manager.unsubscribe_task(task_id, q)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@main_bp.route('/api/logs')
@admin_required
def get_all_logs_api():
    """获取所有日志（非SSE，用于初始化）"""
    limit = request.args.get('limit', 200, type=int)
    logs = log_manager.get_all_logs(limit=limit)
    return jsonify({'data': logs})


@main_bp.route('/api/logs/<task_id>')
@login_required
def get_task_logs_api(task_id: str):
    """获取指定任务日志"""
    limit = request.args.get('limit', 100, type=int)
    logs = log_manager.get_logs(task_id, limit=limit)
    return jsonify({'data': logs})


@main_bp.route('/api/logs', methods=['DELETE'])
@admin_required
def clear_all_logs_api():
    """清除所有日志"""
    log_manager.clear_all_logs()
    return jsonify({'message': '日志已清除'})