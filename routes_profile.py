import asyncio
from flask import Blueprint, render_template, request, jsonify, g, send_file

import database
from auth import login_required, get_current_user
from routes import _fetch_user_avatar

# 创建个人资料蓝图
profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def profile_page():
    """个人资料页面"""
    return send_file('vue/dist/index.html')


@profile_bp.route('/api/profile')
@login_required
def get_profile():
    """获取个人资料"""
    user = get_current_user()
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'nickname': user['nickname'],
        'email': user['email'],
        'twitter_id': user['twitter_id'],
        'avatar_url': user['avatar_url'],
        'role': user['role'],
        'created_at': user['created_at']
    })


@profile_bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新个人资料"""
    user = get_current_user()
    data = request.get_json()
    
    nickname = (data.get('nickname') or '').strip()
    email = (data.get('email') or '').strip()
    
    # 更新资料
    update_data = {}
    if nickname:
        update_data['nickname'] = nickname
    if email:
        update_data['email'] = email
    
    if update_data:
        database.update_user(user['id'], **update_data)
    
    return jsonify({'message': '资料已更新'})


@profile_bp.route('/api/profile/twitter-id', methods=['PUT'])
@login_required
def update_twitter_id():
    """更新推特ID并获取头像"""
    user = get_current_user()
    data = request.get_json()
    
    twitter_id = (data.get('twitter_id') or '').strip()
    
    # 更新推特ID
    database.update_user(user['id'], twitter_id=twitter_id)
    
    # 如果设置了推特ID，尝试获取头像
    avatar_url = None
    if twitter_id:
        try:
            loop = asyncio.new_event_loop()
            avatar_url = loop.run_until_complete(_fetch_user_avatar(twitter_id))
            loop.close()
            
            if avatar_url:
                database.update_user(user['id'], avatar_url=avatar_url)
        except Exception as e:
            print(f"获取头像失败: {e}")
    
    return jsonify({
        'message': '推特ID已更新',
        'twitter_id': twitter_id,
        'avatar_url': avatar_url
    })


@profile_bp.route('/api/profile/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    user = get_current_user()
    data = request.get_json()
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # 验证必填字段
    if not old_password or not new_password or not confirm_password:
        return jsonify({'error': '请填写所有密码字段'}), 400
    
    # 验证新密码长度
    if len(new_password) < 6:
        return jsonify({'error': '新密码长度不能少于6个字符'}), 400
    
    # 验证两次密码是否一致
    if new_password != confirm_password:
        return jsonify({'error': '两次输入的密码不一致'}), 400
    
    # 验证旧密码
    if not database.verify_password(user['id'], old_password):
        return jsonify({'error': '旧密码错误'}), 400
    
    # 更新密码
    database.update_user(user['id'], password=new_password)
    
    return jsonify({'message': '密码已修改'})
