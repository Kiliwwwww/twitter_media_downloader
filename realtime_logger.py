import time
import threading
import queue
from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: float
    task_id: str
    user_id: str
    level: str  # info, warning, error, success
    message: str
    category: str = ''  # download, system, etc
    
    def to_dict(self):
        return asdict(self)
    
    def format_time(self):
        return time.strftime('%H:%M:%S', time.localtime(self.timestamp))


class RealtimeLogManager:
    """实时日志管理器"""
    
    def __init__(self, max_logs_per_task: int = 1000, max_total_logs: int = 5000):
        self._logs: Dict[str, list] = {}  # task_id -> [LogEntry]
        self._subscribers: Dict[str, list] = {}  # task_id -> [queue.Queue]
        self._global_subscribers: list = []  # 全局订阅者
        self._lock = threading.Lock()
        self._max_logs_per_task = max_logs_per_task
        self._max_total_logs = max_total_logs
    
    def add_log(self, task_id: str, user_id: str, level: str, message: str, category: str = ''):
        """添加日志"""
        entry = LogEntry(
            timestamp=time.time(),
            task_id=task_id,
            user_id=user_id,
            level=level,
            message=message,
            category=category
        )
        
        with self._lock:
            # 存储日志
            if task_id not in self._logs:
                self._logs[task_id] = []
            self._logs[task_id].append(entry)
            
            # 限制日志数量
            if len(self._logs[task_id]) > self._max_logs_per_task:
                self._logs[task_id] = self._logs[task_id][-self._max_logs_per_task:]
            
            # 推送给任务订阅者
            if task_id in self._subscribers:
                for q in self._subscribers[task_id]:
                    try:
                        q.put_nowait(entry)
                    except queue.Full:
                        pass
            
            # 推送给全局订阅者
            for q in self._global_subscribers:
                try:
                    q.put_nowait(entry)
                except queue.Full:
                    pass
    
    def info(self, task_id: str, user_id: str, message: str, category: str = ''):
        """添加info日志"""
        self.add_log(task_id, user_id, 'info', message, category)
    
    def success(self, task_id: str, user_id: str, message: str, category: str = ''):
        """添加成功日志"""
        self.add_log(task_id, user_id, 'success', message, category)
    
    def warning(self, task_id: str, user_id: str, message: str, category: str = ''):
        """添加警告日志"""
        self.add_log(task_id, user_id, 'warning', message, category)
    
    def error(self, task_id: str, user_id: str, message: str, category: str = ''):
        """添加错误日志"""
        self.add_log(task_id, user_id, 'error', message, category)
    
    def get_logs(self, task_id: str, limit: int = 100) -> list:
        """获取任务日志"""
        with self._lock:
            logs = self._logs.get(task_id, [])
            return [log.to_dict() for log in logs[-limit:]]
    
    def get_all_logs(self, limit: int = 200) -> list:
        """获取所有日志（按时间排序）"""
        with self._lock:
            all_logs = []
            for logs in self._logs.values():
                all_logs.extend(logs)
            # 按时间倒序
            all_logs.sort(key=lambda x: x.timestamp, reverse=True)
            return [log.to_dict() for log in all_logs[:limit]]
    
    def subscribe_task(self, task_id: str) -> queue.Queue:
        """订阅任务日志"""
        q = queue.Queue(maxsize=500)
        with self._lock:
            if task_id not in self._subscribers:
                self._subscribers[task_id] = []
            self._subscribers[task_id].append(q)
        return q
    
    def subscribe_all(self) -> queue.Queue:
        """订阅所有日志"""
        q = queue.Queue(maxsize=500)
        with self._lock:
            self._global_subscribers.append(q)
        return q
    
    def unsubscribe_task(self, task_id: str, q: queue.Queue):
        """取消订阅任务日志"""
        with self._lock:
            if task_id in self._subscribers:
                try:
                    self._subscribers[task_id].remove(q)
                except ValueError:
                    pass
    
    def unsubscribe_all(self, q: queue.Queue):
        """取消全局订阅"""
        with self._lock:
            try:
                self._global_subscribers.remove(q)
            except ValueError:
                pass
    
    def clear_task_logs(self, task_id: str):
        """清除任务日志"""
        with self._lock:
            if task_id in self._logs:
                del self._logs[task_id]
    
    def clear_all_logs(self):
        """清除所有日志"""
        with self._lock:
            self._logs.clear()


# 全局实例
log_manager = RealtimeLogManager()
