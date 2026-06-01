import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

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
        
        # 创建配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建下载历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT,
                status TEXT NOT NULL,
                total_files INTEGER DEFAULT 0,
                downloaded_files INTEGER DEFAULT 0,
                file_size INTEGER DEFAULT 0,
                zip_path TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # 插入默认配置
        default_configs = [
            ('proxy', '', '代理地址（如: http://127.0.0.1:7890）'),
            ('auth_token', '', 'auth_token'),
            ('ct0', '', 'ct0'),
        ]
        
        for key, value, description in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO config (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, description))


def get_config(key: str) -> Optional[str]:
    """获取配置值"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else None


def get_all_configs() -> List[Dict[str, Any]]:
    """获取所有配置"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key, value, description, updated_at FROM config ORDER BY key')
        return [dict(row) for row in cursor.fetchall()]


def update_config(key: str, value: str):
    """更新配置"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE config SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = ?
        ''', (value, key))


def add_download_history(task_id: str, user_id: str, user_name: str = None):
    """添加下载历史"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO download_history (task_id, user_id, user_name, status)
            VALUES (?, ?, ?, 'downloading')
        ''', (task_id, user_id, user_name))


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


def get_download_history(limit: int = 50, offset: int = 0, keyword: str = '', status: str = '', date: str = '') -> List[Dict[str, Any]]:
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


def get_download_history_count(keyword: str = '', status: str = '', date: str = '') -> int:
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