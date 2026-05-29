import os
from flask import Blueprint, render_template, request, jsonify, send_file

from config import Config
from services import download_service
import database

# 创建蓝图
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')


@main_bp.route('/config')
def config_page():
    """配置管理页面"""
    return render_template('config.html')


@main_bp.route('/history')
def history_page():
    """下载历史页面"""
    return render_template('history.html')


@main_bp.route('/api/download', methods=['POST'])
def start_download():
    """开始下载"""
    data = request.get_json()
    user_id = data.get('user_id', '').strip()
    
    if not user_id:
        return jsonify({'error': '请输入用户ID'}), 400
    
    # 创建下载任务
    task = download_service.create_task(user_id)
    
    return jsonify({
        'task_id': task.task_id,
        'message': f'开始下载用户 {user_id} 的媒体文件'
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
    
    return send_file(
        task.zip_path,
        as_attachment=True,
        download_name=f'{task.user_id}_media.zip'
    )


# 配置管理API
@main_bp.route('/api/configs')
def get_configs():
    """获取所有配置"""
    configs = database.get_all_configs()
    return jsonify(configs)


@main_bp.route('/api/configs', methods=['PUT'])
def update_configs():
    """更新配置"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的数据'}), 400
    
    try:
        for key, value in data.items():
            database.update_config(key, value)
        return jsonify({'message': '配置已更新'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 下载历史API
@main_bp.route('/api/history')
def get_history():
    """获取下载历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    offset = (page - 1) * per_page
    history = database.get_download_history(limit=per_page, offset=offset)
    total = database.get_download_history_count()
    
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