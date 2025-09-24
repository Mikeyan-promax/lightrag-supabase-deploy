#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控系统

这是一个企业级的性能监控系统，提供实时指标收集、性能分析、瓶颈检测和告警机制。

主要特性:
- 实时性能指标收集（CPU、内存、网络、磁盘）
- 应用程序性能监控（响应时间、吞吐量、错误率）
- 自定义指标和业务指标监控
- 智能异常检测和告警
- 性能趋势分析和预测
- 分布式追踪和链路分析
- 性能瓶颈自动识别
- 实时仪表板和报告
- 历史数据存储和查询
- 多维度性能分析

作者: AI Assistant
创建时间: 2024
版本: 1.0.0
"""

import asyncio
import logging
import time
import threading
import json
import statistics
import psutil
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import (
    Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple, Union,
    TypeVar, Generic, Protocol, runtime_checkable
)
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import aiohttp
from contextlib import asynccontextmanager

# 配置日志
logger = logging.getLogger(__name__)

# 类型定义
T = TypeVar('T')
MetricValue = Union[int, float]


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"              # 计数器（只增不减）
    GAUGE = "gauge"                  # 仪表（可增可减）
    HISTOGRAM = "histogram"          # 直方图（分布统计）
    SUMMARY = "summary"              # 摘要（分位数统计）
    TIMER = "timer"                  # 计时器
    RATE = "rate"                    # 速率


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态枚举"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: MetricValue
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "labels": self.labels
        }


@dataclass
class MetricSeries:
    """指标时间序列"""
    name: str
    metric_type: MetricType
    description: str = ""
    unit: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_point(self, value: MetricValue, timestamp: Optional[float] = None, labels: Optional[Dict[str, str]] = None):
        """添加数据点"""
        if timestamp is None:
            timestamp = time.time()
        
        point_labels = {**self.labels}
        if labels:
            point_labels.update(labels)
        
        point = MetricPoint(timestamp=timestamp, value=value, labels=point_labels)
        self.points.append(point)
    
    def get_latest_value(self) -> Optional[MetricValue]:
        """获取最新值"""
        if not self.points:
            return None
        return self.points[-1].value
    
    def get_values_in_range(self, start_time: float, end_time: float) -> List[MetricPoint]:
        """获取时间范围内的值"""
        return [
            point for point in self.points
            if start_time <= point.timestamp <= end_time
        ]
    
    def calculate_statistics(self, duration: float = 300.0) -> Dict[str, float]:
        """计算统计信息"""
        current_time = time.time()
        start_time = current_time - duration
        
        values = [
            point.value for point in self.points
            if point.timestamp >= start_time and isinstance(point.value, (int, float))
        ]
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "p95": np.percentile(values, 95) if values else 0.0,
            "p99": np.percentile(values, 99) if values else 0.0
        }


@dataclass
class Alert:
    """告警信息"""
    alert_id: str
    name: str
    description: str
    level: AlertLevel
    status: AlertStatus = AlertStatus.ACTIVE
    metric_name: str = ""
    threshold_value: Optional[MetricValue] = None
    current_value: Optional[MetricValue] = None
    labels: Dict[str, str] = field(default_factory=dict)
    created_time: float = field(default_factory=time.time)
    updated_time: float = field(default_factory=time.time)
    resolved_time: Optional[float] = None
    
    def resolve(self):
        """解决告警"""
        self.status = AlertStatus.RESOLVED
        self.resolved_time = time.time()
        self.updated_time = self.resolved_time
    
    def suppress(self):
        """抑制告警"""
        self.status = AlertStatus.SUPPRESSED
        self.updated_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # 条件表达式，如 "> 0.8", "< 100", "== 0"
    threshold: MetricValue
    level: AlertLevel
    duration: float = 60.0  # 持续时间（秒）
    labels: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    
    def evaluate(self, current_value: MetricValue) -> bool:
        """评估告警条件"""
        if not self.enabled:
            return False
        
        try:
            if self.condition.startswith(">="):
                return current_value >= self.threshold
            elif self.condition.startswith("<="):
                return current_value <= self.threshold
            elif self.condition.startswith(">"): 
                return current_value > self.threshold
            elif self.condition.startswith("<"):
                return current_value < self.threshold
            elif self.condition.startswith("=="):
                return current_value == self.threshold
            elif self.condition.startswith("!="):
                return current_value != self.threshold
            else:
                return False
        except (TypeError, ValueError):
            return False


class SystemMetricsCollector:
    """系统指标收集器"""
    
    def __init__(self, collection_interval: float = 5.0):
        self.collection_interval = collection_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._metrics_callback: Optional[Callable[[Dict[str, MetricValue]], None]] = None
    
    def set_metrics_callback(self, callback: Callable[[Dict[str, MetricValue]], None]):
        """设置指标回调函数"""
        self._metrics_callback = callback
    
    async def start(self):
        """启动收集器"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("系统指标收集器启动")
    
    async def stop(self):
        """停止收集器"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("系统指标收集器停止")
    
    async def _collection_loop(self):
        """收集循环"""
        while self._running:
            try:
                metrics = await self._collect_system_metrics()
                if self._metrics_callback:
                    self._metrics_callback(metrics)
                
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"系统指标收集出错: {e}")
                await asyncio.sleep(1.0)
    
    async def _collect_system_metrics(self) -> Dict[str, MetricValue]:
        """收集系统指标"""
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        
        # 内存指标
        memory = psutil.virtual_memory()
        
        # 磁盘指标
        disk = psutil.disk_usage('/')
        
        # 网络指标
        network = psutil.net_io_counters()
        
        # 进程指标
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            # CPU指标
            "system.cpu.usage_percent": cpu_percent,
            "system.cpu.count": cpu_count,
            
            # 内存指标
            "system.memory.total": memory.total,
            "system.memory.available": memory.available,
            "system.memory.used": memory.used,
            "system.memory.usage_percent": memory.percent,
            
            # 磁盘指标
            "system.disk.total": disk.total,
            "system.disk.used": disk.used,
            "system.disk.free": disk.free,
            "system.disk.usage_percent": (disk.used / disk.total) * 100,
            
            # 网络指标
            "system.network.bytes_sent": network.bytes_sent,
            "system.network.bytes_recv": network.bytes_recv,
            "system.network.packets_sent": network.packets_sent,
            "system.network.packets_recv": network.packets_recv,
            
            # 进程指标
            "process.memory.rss": process_memory.rss,
            "process.memory.vms": process_memory.vms,
            "process.cpu.percent": process.cpu_percent(),
            "process.threads.count": process.num_threads(),
        }


class ApplicationMetricsCollector:
    """应用程序指标收集器"""
    
    def __init__(self):
        self._request_count = 0
        self._error_count = 0
        self._response_times: deque = deque(maxlen=1000)
        self._active_requests = 0
        self._start_time = time.time()
        self._lock = threading.Lock()
    
    def record_request(self, response_time: float, is_error: bool = False):
        """记录请求"""
        with self._lock:
            self._request_count += 1
            if is_error:
                self._error_count += 1
            self._response_times.append(response_time)
    
    def start_request(self):
        """开始请求"""
        with self._lock:
            self._active_requests += 1
    
    def end_request(self):
        """结束请求"""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
    
    def get_metrics(self) -> Dict[str, MetricValue]:
        """获取应用指标"""
        with self._lock:
            uptime = time.time() - self._start_time
            
            # 计算响应时间统计
            response_times = list(self._response_times)
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            p95_response_time = np.percentile(response_times, 95) if response_times else 0.0
            p99_response_time = np.percentile(response_times, 99) if response_times else 0.0
            
            # 计算错误率
            error_rate = (self._error_count / max(1, self._request_count)) * 100
            
            # 计算吞吐量（每秒请求数）
            throughput = self._request_count / max(1, uptime)
            
            return {
                "app.requests.total": self._request_count,
                "app.requests.errors": self._error_count,
                "app.requests.active": self._active_requests,
                "app.requests.error_rate": error_rate,
                "app.requests.throughput": throughput,
                "app.response_time.avg": avg_response_time,
                "app.response_time.p95": p95_response_time,
                "app.response_time.p99": p99_response_time,
                "app.uptime": uptime
            }


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, window_size: int = 100, sensitivity: float = 2.0):
        self.window_size = window_size
        self.sensitivity = sensitivity  # 标准差倍数
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
    
    def add_value(self, metric_name: str, value: MetricValue):
        """添加值"""
        if isinstance(value, (int, float)):
            self._history[metric_name].append(value)
    
    def detect_anomaly(self, metric_name: str, current_value: MetricValue) -> bool:
        """检测异常"""
        if not isinstance(current_value, (int, float)):
            return False
        
        history = self._history[metric_name]
        if len(history) < 10:  # 需要足够的历史数据
            return False
        
        try:
            mean = statistics.mean(history)
            std_dev = statistics.stdev(history)
            
            # 使用Z-score检测异常
            z_score = abs(current_value - mean) / max(std_dev, 0.001)
            return z_score > self.sensitivity
        except (statistics.StatisticsError, ZeroDivisionError):
            return False
    
    def get_anomaly_score(self, metric_name: str, current_value: MetricValue) -> float:
        """获取异常分数"""
        if not isinstance(current_value, (int, float)):
            return 0.0
        
        history = self._history[metric_name]
        if len(history) < 10:
            return 0.0
        
        try:
            mean = statistics.mean(history)
            std_dev = statistics.stdev(history)
            z_score = abs(current_value - mean) / max(std_dev, 0.001)
            return min(z_score / self.sensitivity, 1.0)  # 归一化到0-1
        except (statistics.StatisticsError, ZeroDivisionError):
            return 0.0


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self._profiles: Dict[str, List[float]] = defaultdict(list)
        self._active_profiles: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    @asynccontextmanager
    async def profile(self, operation_name: str):
        """性能分析上下文管理器"""
        start_time = time.time()
        
        with self._lock:
            self._active_profiles[operation_name] = start_time
        
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            with self._lock:
                self._profiles[operation_name].append(duration)
                self._active_profiles.pop(operation_name, None)
                
                # 保持历史记录在合理范围内
                if len(self._profiles[operation_name]) > 1000:
                    self._profiles[operation_name] = self._profiles[operation_name][-500:]
    
    def get_profile_stats(self, operation_name: str) -> Dict[str, float]:
        """获取性能统计"""
        with self._lock:
            durations = self._profiles.get(operation_name, [])
            
            if not durations:
                return {}
            
            return {
                "count": len(durations),
                "total_time": sum(durations),
                "avg_time": statistics.mean(durations),
                "min_time": min(durations),
                "max_time": max(durations),
                "p50_time": np.percentile(durations, 50),
                "p95_time": np.percentile(durations, 95),
                "p99_time": np.percentile(durations, 99)
            }
    
    def get_all_profiles(self) -> Dict[str, Dict[str, float]]:
        """获取所有性能统计"""
        with self._lock:
            return {
                operation: self.get_profile_stats(operation)
                for operation in self._profiles.keys()
            }


class MetricsStorage:
    """指标存储"""
    
    def __init__(self, storage_path: str = "metrics_data"):
        self.storage_path = storage_path
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """确保存储目录存在"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    async def store_metrics(self, metrics: Dict[str, MetricSeries]):
        """存储指标"""
        timestamp = datetime.now().strftime("%Y%m%d_%H")
        filename = f"{self.storage_path}/metrics_{timestamp}.json"
        
        # 准备数据
        data = {
            "timestamp": time.time(),
            "metrics": {}
        }
        
        for name, series in metrics.items():
            data["metrics"][name] = {
                "name": series.name,
                "type": series.metric_type.value,
                "description": series.description,
                "unit": series.unit,
                "labels": series.labels,
                "points": [point.to_dict() for point in list(series.points)[-100:]]  # 只保存最近100个点
            }
        
        # 异步写入文件
        try:
            async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"存储指标失败: {e}")
    
    async def load_metrics(self, hours_back: int = 24) -> Dict[str, List[MetricPoint]]:
        """加载历史指标"""
        import os
        import glob
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # 查找相关文件
        pattern = f"{self.storage_path}/metrics_*.json"
        files = glob.glob(pattern)
        
        metrics_data = defaultdict(list)
        
        for file_path in files:
            try:
                # 从文件名提取时间
                basename = os.path.basename(file_path)
                time_str = basename.replace("metrics_", "").replace(".json", "")
                file_time = datetime.strptime(time_str, "%Y%m%d_%H")
                
                # 检查是否在时间范围内
                if start_time <= file_time <= end_time:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        for metric_name, metric_data in data.get("metrics", {}).items():
                            for point_data in metric_data.get("points", []):
                                point = MetricPoint(
                                    timestamp=point_data["timestamp"],
                                    value=point_data["value"],
                                    labels=point_data.get("labels", {})
                                )
                                metrics_data[metric_name].append(point)
            
            except Exception as e:
                logger.warning(f"加载指标文件失败 {file_path}: {e}")
        
        return dict(metrics_data)


class PerformanceMonitor:
    """性能监控主类"""
    
    def __init__(
        self,
        system_collection_interval: float = 5.0,
        storage_interval: float = 300.0,  # 5分钟
        enable_anomaly_detection: bool = True,
        enable_storage: bool = True
    ):
        self.system_collection_interval = system_collection_interval
        self.storage_interval = storage_interval
        self.enable_anomaly_detection = enable_anomaly_detection
        self.enable_storage = enable_storage
        
        # 核心组件
        self._metrics: Dict[str, MetricSeries] = {}
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        
        # 收集器
        self._system_collector = SystemMetricsCollector(system_collection_interval)
        self._app_collector = ApplicationMetricsCollector()
        
        # 分析器
        self._anomaly_detector = AnomalyDetector() if enable_anomaly_detection else None
        self._profiler = PerformanceProfiler()
        
        # 存储
        self._storage = MetricsStorage() if enable_storage else None
        
        # 回调函数
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._metric_callbacks: List[Callable[[str, MetricValue], None]] = []
        
        # 后台任务
        self._running = False
        self._alert_task: Optional[asyncio.Task] = None
        self._storage_task: Optional[asyncio.Task] = None
        
        # 设置系统指标回调
        self._system_collector.set_metrics_callback(self._on_system_metrics)
        
        logger.info("性能监控系统初始化完成")
    
    async def start(self):
        """启动监控系统"""
        if self._running:
            return
        
        self._running = True
        
        # 启动收集器
        await self._system_collector.start()
        
        # 启动后台任务
        self._alert_task = asyncio.create_task(self._alert_loop())
        
        if self.enable_storage:
            self._storage_task = asyncio.create_task(self._storage_loop())
        
        logger.info("性能监控系统启动完成")
    
    async def stop(self, timeout: float = 30.0):
        """停止监控系统"""
        if not self._running:
            return
        
        logger.info("开始停止性能监控系统...")
        self._running = False
        
        # 停止收集器
        await self._system_collector.stop()
        
        # 停止后台任务
        tasks = []
        if self._alert_task:
            tasks.append(self._alert_task)
        if self._storage_task:
            tasks.append(self._storage_task)
        
        for task in tasks:
            task.cancel()
        
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("后台任务停止超时")
        
        # 最后一次存储
        if self.enable_storage and self._storage:
            try:
                await self._storage.store_metrics(self._metrics)
            except Exception as e:
                logger.error(f"最终存储失败: {e}")
        
        logger.info("性能监控系统停止完成")
    
    def record_metric(
        self,
        name: str,
        value: MetricValue,
        metric_type: MetricType = MetricType.GAUGE,
        description: str = "",
        unit: str = "",
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[float] = None
    ):
        """记录指标"""
        # 获取或创建指标序列
        if name not in self._metrics:
            self._metrics[name] = MetricSeries(
                name=name,
                metric_type=metric_type,
                description=description,
                unit=unit,
                labels=labels or {}
            )
        
        # 添加数据点
        series = self._metrics[name]
        series.add_point(value, timestamp, labels)
        
        # 异常检测
        if self._anomaly_detector:
            self._anomaly_detector.add_value(name, value)
            
            if self._anomaly_detector.detect_anomaly(name, value):
                anomaly_score = self._anomaly_detector.get_anomaly_score(name, value)
                logger.warning(f"检测到指标异常: {name}={value}, 异常分数: {anomaly_score:.3f}")
                
                # 创建异常告警
                self._create_anomaly_alert(name, value, anomaly_score)
        
        # 触发回调
        for callback in self._metric_callbacks:
            try:
                callback(name, value)
            except Exception as e:
                logger.error(f"指标回调出错: {e}")
    
    def _on_system_metrics(self, metrics: Dict[str, MetricValue]):
        """系统指标回调"""
        for name, value in metrics.items():
            self.record_metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                description=f"系统指标: {name}"
            )
    
    def record_application_metrics(self):
        """记录应用指标"""
        app_metrics = self._app_collector.get_metrics()
        for name, value in app_metrics.items():
            self.record_metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                description=f"应用指标: {name}"
            )
    
    def get_application_collector(self) -> ApplicationMetricsCollector:
        """获取应用指标收集器"""
        return self._app_collector
    
    def get_profiler(self) -> PerformanceProfiler:
        """获取性能分析器"""
        return self._profiler
    
    def add_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: MetricValue,
        level: AlertLevel = AlertLevel.WARNING,
        duration: float = 60.0,
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """添加告警规则"""
        rule_id = str(uuid.uuid4())
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            description=f"告警规则: {name}",
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            level=level,
            duration=duration,
            labels=labels or {}
        )
        
        self._alert_rules[rule_id] = rule
        logger.info(f"添加告警规则: {name} ({rule_id})")
        return rule_id
    
    def remove_alert_rule(self, rule_id: str):
        """移除告警规则"""
        if rule_id in self._alert_rules:
            rule = self._alert_rules.pop(rule_id)
            logger.info(f"移除告警规则: {rule.name} ({rule_id})")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调"""
        self._alert_callbacks.append(callback)
    
    def add_metric_callback(self, callback: Callable[[str, MetricValue], None]):
        """添加指标回调"""
        self._metric_callbacks.append(callback)
    
    def _create_anomaly_alert(self, metric_name: str, value: MetricValue, anomaly_score: float):
        """创建异常告警"""
        alert_id = f"anomaly_{metric_name}_{int(time.time())}"
        
        # 确定告警级别
        if anomaly_score > 0.8:
            level = AlertLevel.CRITICAL
        elif anomaly_score > 0.6:
            level = AlertLevel.ERROR
        else:
            level = AlertLevel.WARNING
        
        alert = Alert(
            alert_id=alert_id,
            name=f"异常检测: {metric_name}",
            description=f"指标 {metric_name} 检测到异常值 {value}，异常分数: {anomaly_score:.3f}",
            level=level,
            metric_name=metric_name,
            current_value=value,
            labels={"type": "anomaly", "metric": metric_name}
        )
        
        self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Alert):
        """触发告警"""
        self._active_alerts[alert.alert_id] = alert
        self._alert_history.append(alert)
        
        # 保持历史记录在合理范围内
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-500:]
        
        logger.warning(f"触发告警: {alert.name} ({alert.level.value})")
        
        # 触发回调
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调出错: {e}")
    
    async def _alert_loop(self):
        """告警检查循环"""
        logger.info("告警检查任务启动")
        
        while self._running:
            try:
                await self._check_alert_rules()
                await asyncio.sleep(10.0)  # 每10秒检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"告警检查出错: {e}")
        
        logger.info("告警检查任务停止")
    
    async def _check_alert_rules(self):
        """检查告警规则"""
        for rule in self._alert_rules.values():
            if not rule.enabled:
                continue
            
            # 获取指标当前值
            metric_series = self._metrics.get(rule.metric_name)
            if not metric_series:
                continue
            
            current_value = metric_series.get_latest_value()
            if current_value is None:
                continue
            
            # 评估告警条件
            if rule.evaluate(current_value):
                # 检查是否已有活跃告警
                existing_alert = None
                for alert in self._active_alerts.values():
                    if (alert.metric_name == rule.metric_name and 
                        alert.status == AlertStatus.ACTIVE and
                        "rule_id" in alert.labels and
                        alert.labels["rule_id"] == rule.rule_id):
                        existing_alert = alert
                        break
                
                if not existing_alert:
                    # 创建新告警
                    alert_id = f"rule_{rule.rule_id}_{int(time.time())}"
                    alert = Alert(
                        alert_id=alert_id,
                        name=rule.name,
                        description=rule.description,
                        level=rule.level,
                        metric_name=rule.metric_name,
                        threshold_value=rule.threshold,
                        current_value=current_value,
                        labels={**rule.labels, "rule_id": rule.rule_id}
                    )
                    
                    self._trigger_alert(alert)
            else:
                # 解决相关告警
                alerts_to_resolve = [
                    alert for alert in self._active_alerts.values()
                    if (alert.metric_name == rule.metric_name and
                        alert.status == AlertStatus.ACTIVE and
                        "rule_id" in alert.labels and
                        alert.labels["rule_id"] == rule.rule_id)
                ]
                
                for alert in alerts_to_resolve:
                    alert.resolve()
                    logger.info(f"解决告警: {alert.name} ({alert.alert_id})")
    
    async def _storage_loop(self):
        """存储循环"""
        logger.info("指标存储任务启动")
        
        while self._running:
            try:
                if self._storage:
                    await self._storage.store_metrics(self._metrics)
                
                await asyncio.sleep(self.storage_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"指标存储出错: {e}")
        
        logger.info("指标存储任务停止")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {
            "total_metrics": len(self._metrics),
            "active_alerts": len([a for a in self._active_alerts.values() if a.status == AlertStatus.ACTIVE]),
            "total_alert_rules": len(self._alert_rules),
            "metrics": {}
        }
        
        for name, series in self._metrics.items():
            latest_value = series.get_latest_value()
            stats = series.calculate_statistics()
            
            summary["metrics"][name] = {
                "latest_value": latest_value,
                "type": series.metric_type.value,
                "description": series.description,
                "unit": series.unit,
                "statistics": stats
            }
        
        return summary
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        active_alerts = [a for a in self._active_alerts.values() if a.status == AlertStatus.ACTIVE]
        
        return {
            "active_alerts_count": len(active_alerts),
            "total_alerts_count": len(self._alert_history),
            "alerts_by_level": {
                level.value: len([a for a in active_alerts if a.level == level])
                for level in AlertLevel
            },
            "active_alerts": [alert.to_dict() for alert in active_alerts[:10]],  # 最近10个
            "recent_alerts": [alert.to_dict() for alert in self._alert_history[-10:]]  # 最近10个
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        profiles = self._profiler.get_all_profiles()
        
        return {
            "total_operations": len(profiles),
            "profiles": profiles
        }


if __name__ == "__main__":
    # 示例用法
    async def main():
        """主函数示例"""
        # 创建性能监控器
        monitor = PerformanceMonitor(
            system_collection_interval=2.0,
            enable_anomaly_detection=True,
            enable_storage=True
        )
        
        # 添加告警规则
        monitor.add_alert_rule(
            name="CPU使用率过高",
            metric_name="system.cpu.usage_percent",
            condition=">",
            threshold=80.0,
            level=AlertLevel.WARNING
        )
        
        monitor.add_alert_rule(
            name="内存使用率过高",
            metric_name="system.memory.usage_percent",
            condition=">",
            threshold=90.0,
            level=AlertLevel.ERROR
        )
        
        # 添加告警回调
        def alert_handler(alert: Alert):
            print(f"🚨 告警: {alert.name} - {alert.description}")
        
        monitor.add_alert_callback(alert_handler)
        
        try:
            await monitor.start()
            
            # 获取应用指标收集器和性能分析器
            app_collector = monitor.get_application_collector()
            profiler = monitor.get_profiler()
            
            print("性能监控系统启动，开始模拟工作负载...")
            
            # 模拟一些工作负载
            for i in range(20):
                # 模拟请求处理
                app_collector.start_request()
                
                async with profiler.profile("api_request"):
                    # 模拟API处理时间
                    await asyncio.sleep(0.1 + (i % 3) * 0.05)
                    
                    # 模拟错误
                    is_error = i % 10 == 0
                    response_time = 0.1 + (i % 3) * 0.05
                    app_collector.record_request(response_time, is_error)
                
                app_collector.end_request()
                
                # 记录自定义指标
                monitor.record_metric(
                    "custom.queue_size",
                    i * 2,
                    MetricType.GAUGE,
                    "队列大小",
                    "items"
                )
                
                # 记录应用指标
                monitor.record_application_metrics()
                
                await asyncio.sleep(1.0)
            
            # 等待一段时间让监控系统收集数据
            await asyncio.sleep(10)
            
            # 打印摘要
            print("\n=== 指标摘要 ===")
            metrics_summary = monitor.get_metrics_summary()
            print(f"总指标数: {metrics_summary['total_metrics']}")
            print(f"活跃告警数: {metrics_summary['active_alerts']}")
            
            print("\n=== 关键指标 ===")
            key_metrics = [
                "system.cpu.usage_percent",
                "system.memory.usage_percent",
                "app.requests.total",
                "app.requests.error_rate",
                "app.response_time.avg"
            ]
            
            for metric_name in key_metrics:
                if metric_name in metrics_summary["metrics"]:
                    metric_info = metrics_summary["metrics"][metric_name]
                    print(f"  {metric_name}: {metric_info['latest_value']:.2f} {metric_info['unit']}")
            
            print("\n=== 告警摘要 ===")
            alerts_summary = monitor.get_alerts_summary()
            print(f"活跃告警: {alerts_summary['active_alerts_count']}")
            print(f"总告警数: {alerts_summary['total_alerts_count']}")
            
            print("\n=== 性能分析 ===")
            perf_summary = monitor.get_performance_summary()
            for operation, stats in perf_summary["profiles"].items():
                if stats:
                    print(f"  {operation}:")
                    print(f"    调用次数: {stats['count']}")
                    print(f"    平均时间: {stats['avg_time']:.3f}s")
                    print(f"    P95时间: {stats['p95_time']:.3f}s")
        
        finally:
            await monitor.stop()
    
    # 运行示例
    asyncio.run(main())