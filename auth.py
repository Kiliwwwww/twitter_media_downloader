from functools import wraps
from flask import session, redirect, url_for, request, jsonify
import database


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            # 如果是API请求，返回401
            if request.path.startswith('/api/'):
                return jsonify({'error': '未登录'}), 401
            # 如果是页面请求，重定向到登录页
            return redirect(url_for('auth.login_page'))
        
        # 验证用户是否存在且启用
        user = database.get_user_by_id(user_id)
        if not user or not user['is_active']:
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({'error': '账号已被禁用'}), 403
            return redirect(url_for('auth.login_page'))
        
        # 将用户信息添加到 g 对象
        from flask import g
        g.current_user = user
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """超管权限装饰器"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        from flask import g
        if g.current_user['role'] != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'error': '权限不足'}), 403
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """获取当前登录用户"""
    from flask import g
    return getattr(g, 'current_user', None)
