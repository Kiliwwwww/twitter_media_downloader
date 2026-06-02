import os
import asyncio
import re
import json
import time
import queue
import httpx
from flask import Blueprint, render_template, request, jsonify, send_file, g, Response

from config import Config
from services import download_service
from realtime_logger import log_manager
import database
from auth import login_required, get_current_user, admin_required

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


@main_bp.route('/api/download', methods=['POST'])
@login_required
def start_download():
    """开始下载"""
    data = request.get_json()
    user_ids = data.get('user_id', '').strip()
    download_type = data.get('download_type', 'all')  # all, video, image
    
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
        task = download_service.create_task(user_id, download_type, account_user_id)
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
        database.delete_download_history(task_id)
        return jsonify({'message': '已删除'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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


@main_bp.route('/api/avatar/<user_id>')
@login_required
def get_user_avatar(user_id: str):
    """获取用户头像"""
    try:
        current_user = get_current_user()
        account_user_id = current_user['id'] if current_user else None
        
        loop = asyncio.new_event_loop()
        avatar_url = loop.run_until_complete(_fetch_user_avatar(user_id, account_user_id=account_user_id))
        loop.close()
        
        if avatar_url:
            # 更新所有该用户的历史记录
            database.update_avatar_by_user_id(user_id, avatar_url)
            return jsonify({'avatar_url': avatar_url})
        
        return jsonify({'avatar_url': None})
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