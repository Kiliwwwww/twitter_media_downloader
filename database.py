import sqlite3
import os
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config


DATABASE_PATH = os.path.join(Config.BASE_DIR, 'data.db')


@contextmanager
def get_db():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 检查 config 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
        config_table_exists = cursor.fetchone()
        
        if config_table_exists:
            # 检查是否有 user_id 字段
            cursor.execute("PRAGMA table_info(config)")
            columns = [col['name'] for col in cursor.fetchall()]
            
            if 'user_id' not in columns:
                # 需要迁移：创建新表并迁移数据
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_new (
                        user_id INTEGER NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, key),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
                
                # 将旧数据迁移到新表（分配给管理员用户 id=1）
                cursor.execute('''
                    INSERT INTO config_new (user_id, key, value, description, updated_at)
                    SELECT 1, key, value, description, updated_at FROM config
                ''')
                
                # 删除旧表
                cursor.execute('DROP TABLE config')
                
                # 重命名新表
                cursor.execute('ALTER TABLE config_new RENAME TO config')
            # 如果已有 user_id 字段，表结构已经正确
        else:
            # 创建配置表（包含 user_id）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    user_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, key),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nickname TEXT,
                email TEXT,
                twitter_id TEXT,
                avatar_url TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建邀请码表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invite_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                created_by INTEGER NOT NULL,
                used_by INTEGER,
                is_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (used_by) REFERENCES users(id)
            )
        ''')
        
        # 创建下载历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT,
                avatar_url TEXT,
                status TEXT NOT NULL,
                total_files INTEGER DEFAULT 0,
                downloaded_files INTEGER DEFAULT 0,
                file_size INTEGER DEFAULT 0,
                zip_path TEXT,
                error_message TEXT,
                account_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (account_user_id) REFERENCES users(id)
            )
        ''')
        
        # 迁移：为现有表添加 avatar_url 字段
        cursor.execute("PRAGMA table_info(download_history)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'avatar_url' not in columns:
            cursor.execute('ALTER TABLE download_history ADD COLUMN avatar_url TEXT')
        
        # 迁移：为现有表添加 account_user_id 字段
        if 'account_user_id' not in columns:
            cursor.execute('ALTER TABLE download_history ADD COLUMN account_user_id INTEGER')
        
        # 迁移：为现有表添加 skipped_files 和 failed_files 字段
        if 'skipped_files' not in columns:
            cursor.execute('ALTER TABLE download_history ADD COLUMN skipped_files INTEGER DEFAULT 0')
        if 'failed_files' not in columns:
            cursor.execute('ALTER TABLE download_history ADD COLUMN failed_files INTEGER DEFAULT 0')
        
        # 创建默认超管账号 admin/123456
        cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        admin_user = cursor.fetchone()
        if not admin_user:
            password_hash = generate_password_hash('123456')
            cursor.execute('''
                INSERT INTO users (username, password_hash, nickname, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', password_hash, '管理员', 'admin', 1))
            admin_id = cursor.lastrowid
        else:
            admin_id = admin_user['id']
        
        # 为管理员用户插入默认配置（如果不存在）
        default_configs = [
            ('proxy', '', '代理地址（如: http://127.0.0.1:7890）'),
            ('auth_token', '', 'auth_token'),
            ('ct0', '', 'ct0'),
        ]
        
        for key, value, description in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO config (user_id, key, value, description)
                VALUES (?, ?, ?, ?)
            ''', (admin_id, key, value, description))


def get_config(key: str, user_id: int = None) -> Optional[str]:
    """获取配置值"""
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute('SELECT value FROM config WHERE key = ? AND user_id = ?', (key, user_id))
        else:
            # 兼容旧逻辑：如果没有 user_id，尝试获取第一个匹配的配置
            cursor.execute('SELECT value FROM config WHERE key = ? LIMIT 1', (key,))
        row = cursor.fetchone()
        return row['value'] if row else None


def get_all_configs(user_id: int = None) -> List[Dict[str, Any]]:
    """获取所有配置"""
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute('SELECT key, value, description, updated_at FROM config WHERE user_id = ? ORDER BY key', (user_id,))
            configs = [dict(row) for row in cursor.fetchall()]
            
            # 如果用户没有配置，自动创建默认配置
            if not configs:
                default_configs = [
                    ('proxy', '', '代理地址（如: http://127.0.0.1:7890）'),
                    ('auth_token', '', 'auth_token'),
                    ('ct0', '', 'ct0'),
                ]
                
                for key, value, description in default_configs:
                    cursor.execute('''
                        INSERT INTO config (user_id, key, value, description)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, key, value, description))
                
                # 重新查询
                cursor.execute('SELECT key, value, description, updated_at FROM config WHERE user_id = ? ORDER BY key', (user_id,))
                configs = [dict(row) for row in cursor.fetchall()]
            
            return configs
        else:
            cursor.execute('SELECT key, value, description, updated_at FROM config ORDER BY key')
            return [dict(row) for row in cursor.fetchall()]


def update_config(key: str, value: str, user_id: int = None):
    """更新配置"""
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id is not None:
            # 先尝试更新
            cursor.execute('''
                UPDATE config SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = ? AND user_id = ?
            ''', (value, key, user_id))
            
            # 如果没有更新任何行，则插入新记录
            if cursor.rowcount == 0:
                # 获取配置描述
                descriptions = {
                    'proxy': '代理地址（如: http://127.0.0.1:7890）',
                    'auth_token': 'auth_token',
                    'ct0': 'ct0',
                    'secret_key': 'Flask session密钥（自动生成）'
                }
                description = descriptions.get(key, key)
                cursor.execute('''
                    INSERT INTO config (user_id, key, value, description)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, key, value, description))
        else:
            # 兼容旧逻辑
            cursor.execute('''
                UPDATE config SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = ?
            ''', (value, key))


def add_download_history(task_id: str, user_id: str, user_name: str = None, account_user_id: int = None):
    """添加下载历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO download_history (task_id, user_id, user_name, status, account_user_id)
            VALUES (?, ?, ?, 'downloading', ?)
        ''', (task_id, user_id, user_name, account_user_id))


def update_download_history(task_id: str, **kwargs):
    """更新下载历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 构建更新语句
        updates = []
        values = []
        for key, value in kwargs.items():
            updates.append(f'{key} = ?')
            values.append(value)
        
        if updates:
            values.append(task_id)
            sql = f'UPDATE download_history SET {", ".join(updates)} WHERE task_id = ?'
            cursor.execute(sql, values)


def get_download_history(limit: int = 50, offset: int = 0, keyword: str = '', status: str = '', date: str = '', account_user_id: int = None) -> List[Dict[str, Any]]:
    """获取下载历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if keyword:
            conditions.append("(user_id LIKE ? OR user_name LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if date:
            conditions.append("DATE(created_at) = ?")
            params.append(date)
        
        # 数据隔离：普通用户只能看到自己的记录
        if account_user_id:
            conditions.append("account_user_id = ?")
            params.append(account_user_id)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        sql = f'''
            SELECT * FROM download_history 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        params.extend([limit, offset])
        
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_download_history_count(keyword: str = '', status: str = '', date: str = '', account_user_id: int = None) -> int:
    """获取下载历史总数"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if keyword:
            conditions.append("(user_id LIKE ? OR user_name LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if date:
            conditions.append("DATE(created_at) = ?")
            params.append(date)
        
        # 数据隔离：普通用户只能看到自己的记录
        if account_user_id:
            conditions.append("account_user_id = ?")
            params.append(account_user_id)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        sql = f'SELECT COUNT(*) as count FROM download_history {where_clause}'
        cursor.execute(sql, params)
        return cursor.fetchone()['count']


def get_download_by_task_id(task_id: str) -> Optional[Dict[str, Any]]:
    """根据任务ID获取下载记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM download_history WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_download_history(task_id: str):
    """删除下载历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM download_history WHERE task_id = ?', (task_id,))


def clear_all_download_history():
    """清空所有下载历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM download_history')


def update_avatar_by_user_id(user_id: str, avatar_url: str):
    """根据用户ID更新头像"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE download_history SET avatar_url = ? WHERE user_id = ? AND (avatar_url IS NULL OR avatar_url = '')
        ''', (avatar_url, user_id))


# ==================== 用户相关函数 ====================

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """根据用户名获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user(username: str, password: str, nickname: str = None, 
                email: str = None, role: str = 'user') -> int:
    """创建用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, nickname, email, role, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (username, password_hash, nickname or username, email, role))
        user_id = cursor.lastrowid
        
        # 为新用户创建默认配置
        default_configs = [
            ('proxy', '', '代理地址（如: http://127.0.0.1:7890）'),
            ('auth_token', '', 'auth_token'),
            ('ct0', '', 'ct0'),
        ]
        
        for key, value, description in default_configs:
            cursor.execute('''
                INSERT INTO config (user_id, key, value, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, key, value, description))
        
        return user_id


def update_user(user_id: int, **kwargs):
    """更新用户信息"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 处理密码字段
        if 'password' in kwargs:
            kwargs['password_hash'] = generate_password_hash(kwargs.pop('password'))
        
        updates = []
        values = []
        for key, value in kwargs.items():
            updates.append(f'{key} = ?')
            values.append(value)
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            values.append(user_id)
            sql = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
            cursor.execute(sql, values)


def delete_user(user_id: int):
    """删除用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))


def get_users_list(page: int = 1, per_page: int = 20, keyword: str = '') -> Dict[str, Any]:
    """获取用户列表"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if keyword:
            conditions.append("(username LIKE ? OR nickname LIKE ? OR email LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 获取总数
        count_sql = f'SELECT COUNT(*) as count FROM users {where_clause}'
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['count']
        
        # 获取分页数据
        offset = (page - 1) * per_page
        data_sql = f'''
            SELECT id, username, nickname, email, twitter_id, avatar_url, role, is_active, created_at, updated_at
            FROM users {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([per_page, offset])
        cursor.execute(data_sql, params)
        users = [dict(row) for row in cursor.fetchall()]
        
        return {
            'data': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }


def toggle_user_active(user_id: int):
    """切换用户启用/禁用状态"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))


def verify_password(user_id: int, password: str) -> bool:
    """验证用户密码"""
    user = get_user_by_id(user_id)
    if not user:
        return False
    return check_password_hash(user['password_hash'], password)


# ==================== 邀请码相关函数 ====================

def create_invite_code(created_by: int) -> str:
    """创建邀请码"""
    code = secrets.token_urlsafe(16)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invite_codes (code, created_by)
            VALUES (?, ?)
        ''', (code, created_by))
    return code


def get_invite_code(code: str) -> Optional[Dict[str, Any]]:
    """获取邀请码信息"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM invite_codes WHERE code = ?', (code,))
        row = cursor.fetchone()
        return dict(row) if row else None


def use_invite_code(code: str, user_id: int) -> bool:
    """使用邀请码"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE invite_codes SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP
            WHERE code = ? AND is_used = 0
        ''', (user_id, code))
        return cursor.rowcount > 0


def get_invite_codes_list(page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """获取邀请码列表"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取总数
        cursor.execute('SELECT COUNT(*) as count FROM invite_codes')
        total = cursor.fetchone()['count']
        
        # 获取分页数据
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT ic.*, u1.username as creator_name, u2.username as used_by_name
            FROM invite_codes ic
            LEFT JOIN users u1 ON ic.created_by = u1.id
            LEFT JOIN users u2 ON ic.used_by = u2.id
            ORDER BY ic.created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        codes = [dict(row) for row in cursor.fetchall()]
        
        return {
            'data': codes,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }


def delete_invite_code(code_id: int):
    """删除邀请码"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM invite_codes WHERE id = ?', (code_id,))