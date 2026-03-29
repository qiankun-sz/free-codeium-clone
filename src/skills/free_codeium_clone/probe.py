"""
探针模块 - 收集用户行为数据和性能指标
集成第一代Token探针，建立基础数据收集能力
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from queue import Queue, Empty
import uuid

from .config import config, ProbeConfig


class ProbeEventType(str, Enum):
    """探针事件类型枚举"""
    REQUEST_START = "request_start"
    API_CALL_START = "api_call_start"
    API_CALL_END = "api_call_end"
    RESPONSE_GENERATED = "response_generated"
    QUALITY_CHECK_DONE = "quality_check_done"
    REQUEST_COMPLETE = "request_complete"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class ProbeEvent:
    """探针事件数据"""
    event_id: str
    event_type: ProbeEventType
    timestamp: str
    session_id: str
    user_id: str
    request_type: str
    language: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, 
              event_type: ProbeEventType,
              session_id: str,
              user_id: str,
              request_type: str,
              language: str,
              data: Dict[str, Any] = None,
              metadata: Dict[str, Any] = None) -> "ProbeEvent":
        """创建探针事件"""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_id=user_id,
            request_type=request_type,
            language=language,
            data=data or {},
            metadata=metadata or {}
        )


@dataclass
class ProbeMetric:
    """探针指标数据"""
    metric_id: str
    name: str
    value: float
    timestamp: str
    session_id: str
    user_id: str
    tags: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def create(cls,
              name: str,
              value: float,
              session_id: str,
              user_id: str,
              tags: Dict[str, str] = None) -> "ProbeMetric":
        """创建探针指标"""
        return cls(
            metric_id=str(uuid.uuid4()),
            name=name,
            value=value,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_id=user_id,
            tags=tags or {}
        )


class ProbeBuffer:
    """探针数据缓冲区"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.events: List[ProbeEvent] = []
        self.metrics: List[ProbeMetric] = []
        self.lock = threading.RLock()
    
    def add_event(self, event: ProbeEvent) -> bool:
        """添加事件到缓冲区"""
        with self.lock:
            if len(self.events) >= self.max_size:
                # 缓冲区满，移除最旧的事件
                self.events.pop(0)
            self.events.append(event)
            return True
    
    def add_metric(self, metric: ProbeMetric) -> bool:
        """添加指标到缓冲区"""
        with self.lock:
            if len(self.metrics) >= self.max_size:
                # 缓冲区满，移除最旧的指标
                self.metrics.pop(0)
            self.metrics.append(metric)
            return True
    
    def get_events(self, limit: int = 100) -> List[ProbeEvent]:
        """获取事件列表"""
        with self.lock:
            return self.events[-limit:] if self.events else []
    
    def get_metrics(self, limit: int = 100) -> List[ProbeMetric]:
        """获取指标列表"""
        with self.lock:
            return self.metrics[-limit:] if self.metrics else []
    
    def clear_events(self):
        """清除事件缓冲区"""
        with self.lock:
            self.events.clear()
    
    def clear_metrics(self):
        """清除指标缓冲区"""
        with self.lock:
            self.metrics.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计信息"""
        with self.lock:
            return {
                "event_count": len(self.events),
                "metric_count": len(self.metrics),
                "max_size": self.max_size
            }


class CentralMetricsService:
    """中心计量服务客户端（模拟实现）"""
    
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or os.getenv("CENTRAL_METRICS_ENDPOINT", "http://localhost:9090/metrics")
        self.logger = logging.getLogger(__name__)
        self.batch_size = 100
        self.queue = Queue(maxsize=1000)
        
        # 启动发送线程
        self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self.sender_thread.start()
        
        self.logger.info(f"中心计量服务客户端初始化完成，端点: {self.endpoint}")
    
    def send_event(self, event: ProbeEvent) -> bool:
        """发送事件到中心服务"""
        try:
            # 在实际实现中，这里应该发送HTTP请求到中心服务
            # 原型阶段记录日志
            event_data = asdict(event)
            self.logger.debug(f"发送事件到中心服务: {event_data}")
            
            # 模拟异步发送
            self.queue.put(event_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"发送事件失败: {e}")
            return False
    
    def send_metric(self, metric: ProbeMetric) -> bool:
        """发送指标到中心服务"""
        try:
            # 在实际实现中，这里应该发送HTTP请求到中心服务
            # 原型阶段记录日志
            metric_data = asdict(metric)
            self.logger.debug(f"发送指标到中心服务: {metric_data}")
            
            # 模拟异步发送
            self.queue.put({"type": "metric", "data": metric_data})
            
            return True
            
        except Exception as e:
            self.logger.error(f"发送指标失败: {e}")
            return False
    
    def _sender_loop(self):
        """发送线程循环"""
        batch = []
        
        while True:
            try:
                # 从队列获取数据
                data = self.queue.get(timeout=1)
                batch.append(data)
                
                # 批量发送
                if len(batch) >= self.batch_size:
                    self._send_batch(batch)
                    batch = []
                    
            except Empty:
                # 队列为空，发送剩余数据
                if batch:
                    self._send_batch(batch)
                    batch = []
                
            except Exception as e:
                self.logger.error(f"发送线程异常: {e}")
                time.sleep(1)
    
    def _send_batch(self, batch: List[Dict[str, Any]]):
        """批量发送数据"""
        try:
            # 在实际实现中，这里应该发送HTTP请求
            # 原型阶段仅记录日志
            self.logger.info(f"批量发送数据到中心服务，数量: {len(batch)}")
            
            # 模拟发送延迟
            time.sleep(0.01)
            
        except Exception as e:
            self.logger.error(f"批量发送失败: {e}")


class ProbeManager:
    """探针管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config.probe_config
        self.buffer = ProbeBuffer()
        
        # 任务队列
        self.task_queue = Queue(maxsize=1000)
        
        # 中心服务客户端
        self.central_service = None
        if self.config.send_to_central_service:
            self.central_service = CentralMetricsService()
        
        # 性能指标
        self.metrics = {
            "events_recorded": 0,
            "metrics_recorded": 0,
            "errors": 0,
            "last_flush_time": time.time(),
            "start_time": time.time()
        }
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        self.logger.info("探针管理器初始化完成（异步模式）")
    
    def record_event(self, 
                    event_type: ProbeEventType,
                    session_id: str,
                    user_id: str,
                    request_type: str,
                    language: str,
                    data: Dict[str, Any] = None,
                    metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        记录探针事件（异步）
        
        Returns:
            事件ID，如果记录失败则返回None
        """
        if not self.config.enabled:
            return None
        
        try:
            # 生成事件ID
            event_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # 创建任务数据
            task_data = {
                'type': 'event',
                'event_id': event_id,
                'event_type': event_type,
                'timestamp': timestamp,
                'session_id': session_id,
                'user_id': user_id,
                'request_type': request_type,
                'language': language,
                'data': data or {},
                'metadata': metadata or {}
            }
            
            # 放入队列（非阻塞）
            try:
                self.task_queue.put(task_data, block=False)
                return event_id
            except queue.Full:
                self.logger.warning(f"探针任务队列已满，丢弃事件: {event_type}")
                self.metrics["errors"] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"记录事件失败: {e}")
            self.metrics["errors"] += 1
            return None
    
    def record_metric(self,
                     name: str,
                     value: float,
                     session_id: str,
                     user_id: str,
                     tags: Dict[str, str] = None) -> Optional[str]:
        """
        记录探针指标（异步）
        
        Returns:
            指标ID，如果记录失败则返回None
        """
        if not self.config.enabled:
            return None
        
        try:
            # 生成指标ID
            metric_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # 创建任务数据
            task_data = {
                'type': 'metric',
                'metric_id': metric_id,
                'name': name,
                'value': value,
                'timestamp': timestamp,
                'session_id': session_id,
                'user_id': user_id,
                'tags': tags or {}
            }
            
            # 放入队列（非阻塞）
            try:
                self.task_queue.put(task_data, block=False)
                return metric_id
            except queue.Full:
                self.logger.warning(f"探针任务队列已满，丢弃指标: {name}")
                self.metrics["errors"] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"记录指标失败: {e}")
            self.metrics["errors"] += 1
            return None
    
    def _worker_loop(self):
        """工作线程循环，处理队列任务"""
        while True:
            try:
                # 从队列获取任务（阻塞，超时1秒）
                task_data = self.task_queue.get(timeout=1)
                
                try:
                    if task_data['type'] == 'event':
                        self._process_event_task(task_data)
                    elif task_data['type'] == 'metric':
                        self._process_metric_task(task_data)
                except Exception as e:
                    self.logger.error(f"处理探针任务失败: {e}")
                    self.metrics["errors"] += 1
                
                # 标记任务完成
                self.task_queue.task_done()
                
            except Empty:
                # 队列为空，继续循环
                continue
            except Exception as e:
                self.logger.error(f"工作线程异常: {e}")
                time.sleep(1)
    
    def _process_event_task(self, task_data: Dict[str, Any]):
        """处理事件任务"""
        # 创建事件对象
        event = ProbeEvent(
            event_id=task_data['event_id'],
            event_type=task_data['event_type'],
            timestamp=task_data['timestamp'],
            session_id=task_data['session_id'],
            user_id=task_data['user_id'],
            request_type=task_data['request_type'],
            language=task_data['language'],
            data=task_data['data'],
            metadata=task_data['metadata']
        )
        
        # 添加到本地缓冲区
        success = self.buffer.add_event(event)
        if success:
            self.metrics["events_recorded"] += 1
        
        # 发送到中心服务
        if self.central_service and self.config.send_to_central_service:
            self.central_service.send_event(event)
    
    def _process_metric_task(self, task_data: Dict[str, Any]):
        """处理指标任务"""
        # 创建指标对象
        metric = ProbeMetric(
            metric_id=task_data['metric_id'],
            name=task_data['name'],
            value=task_data['value'],
            timestamp=task_data['timestamp'],
            session_id=task_data['session_id'],
            user_id=task_data['user_id'],
            tags=task_data['tags']
        )
        
        # 添加到本地缓冲区
        success = self.buffer.add_metric(metric)
        if success:
            self.metrics["metrics_recorded"] += 1
        
        # 发送到中心服务
        if self.central_service and self.config.send_to_central_service:
            self.central_service.send_metric(metric)
    
    # 以下方法保持不变，因为它们只读取数据
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的事件"""
        events = self.buffer.get_events(limit)
        return [asdict(event) for event in events]
    
    def get_recent_metrics(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的指标"""
        metrics = self.buffer.get_metrics(limit)
        return [asdict(metric) for metric in metrics]
    
    def flush_to_storage(self) -> bool:
        """刷新数据到持久化存储"""
        try:
            # 在实际实现中，这里应该将数据保存到数据库或文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"probe_data_{timestamp}.json"
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "events": self.get_recent_events(100),
                "metrics": self.get_recent_metrics(100)
            }
            
            # 原型阶段保存到文件
            probe_dir = "data/probe"
            os.makedirs(probe_dir, exist_ok=True)
            
            filepath = os.path.join(probe_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"探针数据已刷新到存储: {filepath}")
            self.metrics["last_flush_time"] = time.time()
            
            # 清空缓冲区（实际实现中可能只清除已发送的数据）
            self.buffer.clear_events()
            self.buffer.clear_metrics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"刷新数据到存储失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取探针管理器统计信息"""
        return {
            **self.metrics,
            "enabled": self.config.enabled,
            "collect_metrics": self.config.collect_metrics,
            "send_to_central_service": self.config.send_to_central_service and self.central_service is not None,
            "buffer_stats": self.buffer.get_stats(),
            "uptime_hours": round((time.time() - self.metrics.get("start_time", time.time())) / 3600, 2)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.metrics = {
            "events_recorded": 0,
            "metrics_recorded": 0,
            "errors": 0,
            "last_flush_time": time.time(),
            "start_time": time.time()
        }
        self.buffer.clear_events()
        self.buffer.clear_metrics()
        self.logger.info("探针统计信息已重置")


class SessionTracker:
    """会话跟踪器"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        self.lock = threading.RLock()
        
    def create_session(self, user_id: str) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        
        with self.lock:
            self.sessions[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "event_count": 0,
                "total_tokens": 0,
                "requests": []
            }
            
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
        
        return session_id
    
    def update_session(self, 
                      session_id: str,
                      event_data: Dict[str, Any] = None) -> bool:
        """更新会话活动"""
        with self.lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            session["last_activity"] = datetime.now().isoformat()
            
            if event_data:
                session["event_count"] += 1
                session["requests"].append(event_data)
                
                # 累计token消耗
                if "tokens_used" in event_data:
                    session["total_tokens"] += event_data["tokens_used"]
            
            return True
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        with self.lock:
            return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        with self.lock:
            session_ids = self.user_sessions.get(user_id, [])
            return [self.sessions[sid] for sid in session_ids if sid in self.sessions]
    
    def cleanup_inactive_sessions(self, max_inactive_minutes: int = 60):
        """清理不活跃的会话"""
        cutoff_time = datetime.now() - timedelta(minutes=max_inactive_minutes)
        
        with self.lock:
            inactive_sessions = []
            
            for session_id, session in list(self.sessions.items()):
                last_activity = datetime.fromisoformat(session["last_activity"])
                if last_activity < cutoff_time:
                    inactive_sessions.append(session_id)
            
            # 移除不活跃会话
            for session_id in inactive_sessions:
                user_id = self.sessions[session_id]["user_id"]
                self.sessions.pop(session_id, None)
                
                # 从用户会话列表中移除
                if user_id in self.user_sessions:
                    self.user_sessions[user_id] = [
                        sid for sid in self.user_sessions[user_id] 
                        if sid != session_id
                    ]
                    if not self.user_sessions[user_id]:
                        self.user_sessions.pop(user_id, None)
            
            return len(inactive_sessions)


# 全局探针管理器实例
probe_manager = ProbeManager()

# 全局会话跟踪器实例
session_tracker = SessionTracker()


def track_request_start(session_id: str, 
                       user_id: str,
                       request_type: str,
                       language: str) -> Optional[str]:
    """跟踪请求开始事件"""
    return probe_manager.record_event(
        event_type=ProbeEventType.REQUEST_START,
        session_id=session_id,
        user_id=user_id,
        request_type=request_type,
        language=language,
        data={"action": "request_started"}
    )


def track_api_call(session_id: str,
                  user_id: str,
                  request_type: str,
                  language: str,
                  provider: str,
                  input_tokens: int,
                  output_tokens: int) -> List[Optional[str]]:
    """跟踪API调用事件"""
    event_ids = []
    
    # 开始事件
    event_ids.append(probe_manager.record_event(
        event_type=ProbeEventType.API_CALL_START,
        session_id=session_id,
        user_id=user_id,
        request_type=request_type,
        language=language,
        data={
            "provider": provider,
            "input_tokens": input_tokens,
            "action": "api_call_started"
        }
    ))
    
    # 结束事件
    event_ids.append(probe_manager.record_event(
        event_type=ProbeEventType.API_CALL_END,
        session_id=session_id,
        user_id=user_id,
        request_type=request_type,
        language=language,
        data={
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "action": "api_call_completed"
        }
    ))
    
    return event_ids


def track_response_generated(session_id: str,
                            user_id: str,
                            request_type: str,
                            language: str,
                            generated_code: str,
                            quality_score: int) -> Optional[str]:
    """跟踪响应生成事件"""
    return probe_manager.record_event(
        event_type=ProbeEventType.RESPONSE_GENERATED,
        session_id=session_id,
        user_id=user_id,
        request_type=request_type,
        language=language,
        data={
            "generated_code_length": len(generated_code),
            "quality_score": quality_score,
            "action": "response_generated"
        }
    )


def track_quality_check(session_id: str,
                       user_id: str,
                       request_type: str,
                       language: str,
                       passed: bool,
                       issues: List[str],
                       suggestions: List[str]) -> Optional[str]:
    """跟踪质量检查事件"""
    return probe_manager.record_event(
        event_type=ProbeEventType.QUALITY_CHECK_DONE,
        session_id=session_id,
        user_id=user_id,
        request_type=request_type,
        language=language,
        data={
            "passed": passed,
            "issue_count": len(issues),
            "suggestion_count": len(suggestions),
            "action": "quality_check_completed"
        }
    )


def track_request_complete(session_id: str,
                          user_id: str,
                          request_type: str,
                          language: str,
                          success: bool,
                          response_time_ms: float,
                          total_tokens: int) -> Optional[str]:
    """跟踪请求完成事件"""
    return probe_manager.record_event(
        event_type=ProbeEventType.REQUEST_COMPLETE,
        session_id=session_id,
        user_id=user_id,
        request_type=request_type,
        language=language,
        data={
            "success": success,
            "response_time_ms": response_time_ms,
            "total_tokens": total_tokens,
            "action": "request_completed"
        }
    )


def track_error(session_id: str,
               user_id: str,
               request_type: str,
               language: str,
               error_type: str,
               error_message: str) -> Optional[str]:
    """跟踪错误事件"""
    return probe_manager.record_event(
        event_type=ProbeEventType.ERROR_OCCURRED,
        session_id=session_id,
        user_id=user_id,
        request_type=request_type,
        language=language,
        data={
            "error_type": error_type,
            "error_message": error_message,
            "action": "error_occurred"
        }
    )


# 装饰器：自动跟踪函数调用
def probe_tracked(event_name: str = None):
    """装饰器：自动跟踪函数调用"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # 提取上下文信息（需要根据具体函数参数调整）
            context = kwargs.get("context", {})
            session_id = context.get("session_id", "unknown")
            user_id = context.get("user_id", "anonymous")
            request_type = context.get("request_type", "unknown")
            language = context.get("language", "unknown")
            
            # 记录开始事件
            track_request_start(session_id, user_id, request_type, language)
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录成功完成事件
                track_request_complete(
                    session_id=session_id,
                    user_id=user_id,
                    request_type=request_type,
                    language=language,
                    success=True,
                    response_time_ms=0,  # 实际实现中应该计算实际时间
                    total_tokens=0      # 实际实现中应该计算实际token数
                )
                
                return result
                
            except Exception as e:
                # 记录错误事件
                track_error(
                    session_id=session_id,
                    user_id=user_id,
                    request_type=request_type,
                    language=language,
                    error_type=e.__class__.__name__,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    
    return decorator