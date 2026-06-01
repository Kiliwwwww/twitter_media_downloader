from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash
from datetime import timedelta

import database
from auth import login_required, get_current_user

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login_page():
    """登录页面"""
    # 如果已登录，重定向到首页
    if session.get('user_id'):
        return redirect(url_for('main.index'))
    return render_template('login.html')


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录API"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    if not username or not password:
        return jsonify({'error': '请输入用户名和密码'}), 400
    
    # 查找用户
    user = database.get_user_by_username(username)
    if not user:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 验证密码
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 检查用户是否启用
    if not user['is_active']:
        return jsonify({'error': '账号已被禁用，请联系管理员'}), 403
    
    # 设置session
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    
    # 记住我功能：设置session过期时间为30天
    if remember:
        session.permanent = True
    
    return jsonify({
        'message': '登录成功',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'nickname': user['nickname'],
            'role': user['role']
        }
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出API"""
    session.clear()
    return jsonify({'message': '已退出登录'})


@auth_bp.route('/api/auth/me')
@login_required
def get_me():
    """获取当前用户信息"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'nickname': user['nickname'],
        'email': user['email'],
        'twitter_id': user['twitter_id'],
        'avatar_url': user['avatar_url'],
        'role': user['role'],
        'is_active': user['is_active'],
        'created_at': user['created_at']
    })


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册API（需要邀请码）"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    nickname = data.get('nickname', '').strip()
    invite_code = data.get('invite_code', '').strip()
    
    # 验证必填字段
    if not username or not password:
        return jsonify({'error': '请输入用户名和密码'}), 400
    
    if not invite_code:
        return jsonify({'error': '请输入邀请码'}), 400
    
    # 验证用户名长度
    if len(username) < 3 or len(username) > 20:
        return jsonify({'error': '用户名长度应为3-20个字符'}), 400
    
    # 验证密码长度
    if len(password) < 6:
        return jsonify({'error': '密码长度不能少于6个字符'}), 400
    
    # 检查用户名是否已存在
    if database.get_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 400
    
    # 验证邀请码
    code_info = database.get_invite_code(invite_code)
    if not code_info:
        return jsonify({'error': '邀请码不存在'}), 400
    
    if code_info['is_used']:
        return jsonify({'error': '邀请码已被使用'}), 400
    
    # 创建用户
    user_id = database.create_user(
        username=username,
        password=password,
        nickname=nickname or username
    )
    
    # 使用邀请码
    database.use_invite_code(invite_code, user_id)
    
    return jsonify({'message': '注册成功，请登录'}), 201
