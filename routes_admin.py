from flask import Blueprint, render_template, request, jsonify

import database
from auth import admin_required, get_current_user

# 创建管理后台蓝图
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@admin_required
def admin_page():
    """管理后台页面"""
    return render_template('admin.html')


# ==================== 用户管理API ====================

@admin_bp.route('/api/admin/users')
@admin_required
def get_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    
    result = database.get_users_list(page=page, per_page=per_page, keyword=keyword)
    return jsonify(result)


@admin_bp.route('/api/admin/users', methods=['POST'])
@admin_required
def create_user():
    """创建用户"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    nickname = data.get('nickname', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'user')
    
    # 验证必填字段
    if not username or not password:
        return jsonify({'error': '请输入用户名和密码'}), 400
    
    # 验证用户名长度
    if len(username) < 3 or len(username) > 20:
        return jsonify({'error': '用户名长度应为3-20个字符'}), 400
    
    # 验证密码长度
    if len(password) < 6:
        return jsonify({'error': '密码长度不能少于6个字符'}), 400
    
    # 验证角色
    if role not in ['user', 'admin']:
        return jsonify({'error': '无效的角色类型'}), 400
    
    # 检查用户名是否已存在
    if database.get_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 400
    
    # 创建用户
    user_id = database.create_user(
        username=username,
        password=password,
        nickname=nickname or username,
        email=email,
        role=role
    )
    
    return jsonify({'message': '用户创建成功', 'user_id': user_id}), 201


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id: int):
    """更新用户信息"""
    data = request.get_json()
    
    # 检查用户是否存在
    user = database.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 不允许修改超管账号的角色（防止自己降级）
    current_user = get_current_user()
    if user_id == current_user['id'] and data.get('role') != 'admin':
        return jsonify({'error': '不能修改自己的管理员角色'}), 400
    
    # 更新资料
    update_data = {}
    if 'nickname' in data:
        update_data['nickname'] = data['nickname']
    if 'email' in data:
        update_data['email'] = data['email']
    if 'role' in data and user_id != current_user['id']:
        update_data['role'] = data['role']
    
    if update_data:
        database.update_user(user_id, **update_data)
    
    return jsonify({'message': '用户信息已更新'})


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id: int):
    """删除用户"""
    # 检查用户是否存在
    user = database.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 不允许删除自己
    current_user = get_current_user()
    if user_id == current_user['id']:
        return jsonify({'error': '不能删除自己的账号'}), 400
    
    # 不允许删除默认超管
    if user['username'] == 'admin':
        return jsonify({'error': '不能删除默认管理员账号'}), 400
    
    database.delete_user(user_id)
    return jsonify({'message': '用户已删除'})


@admin_bp.route('/api/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id: int):
    """启用/禁用用户"""
    # 检查用户是否存在
    user = database.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 不允许禁用自己
    current_user = get_current_user()
    if user_id == current_user['id']:
        return jsonify({'error': '不能禁用自己的账号'}), 400
    
    # 不允许禁用默认超管
    if user['username'] == 'admin':
        return jsonify({'error': '不能禁用默认管理员账号'}), 400
    
    database.toggle_user_active(user_id)
    
    # 获取更新后的状态
    updated_user = database.get_user_by_id(user_id)
    status = '启用' if updated_user['is_active'] else '禁用'
    
    return jsonify({'message': f'用户已{status}', 'is_active': updated_user['is_active']})


@admin_bp.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id: int):
    """重置用户密码"""
    data = request.get_json()
    new_password = data.get('new_password', '')
    
    # 验证密码
    if not new_password or len(new_password) < 6:
        return jsonify({'error': '密码长度不能少于6个字符'}), 400
    
    # 检查用户是否存在
    user = database.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 更新密码
    database.update_user(user_id, password=new_password)
    
    return jsonify({'message': '密码已重置'})


# ==================== 邀请码管理API ====================

@admin_bp.route('/api/admin/invite-codes')
@admin_required
def get_invite_codes():
    """获取邀请码列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    result = database.get_invite_codes_list(page=page, per_page=per_page)
    return jsonify(result)


@admin_bp.route('/api/admin/invite-codes', methods=['POST'])
@admin_required
def create_invite_code():
    """生成邀请码"""
    count = request.args.get('count', 1, type=int)
    count = min(count, 10)  # 最多一次生成10个
    
    current_user = get_current_user()
    codes = []
    
    for _ in range(count):
        code = database.create_invite_code(current_user['id'])
        codes.append(code)
    
    return jsonify({
        'message': f'已生成 {len(codes)} 个邀请码',
        'codes': codes
    }), 201


@admin_bp.route('/api/admin/invite-codes/<int:code_id>', methods=['DELETE'])
@admin_required
def delete_invite_code(code_id: int):
    """删除邀请码"""
    database.delete_invite_code(code_id)
    return jsonify({'message': '邀请码已删除'})
