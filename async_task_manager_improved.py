#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的异步任务管理器

本模块提供了一个增强的异步任务管理系统，专门用于改善LightRAG中删除操作的稳定性。
主要特性包括：
1. 优先级队列管理
2. 任务取消和清理机制
3. 错误处理和重试逻辑
4. 资源管理和内存优化
5. 并发控制和限流

作者: LightRAG优化团队
创建时间: 2025-01-28
版本: 1.0.0
"""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from functools import partial
import weakref
from contextlib import asynccontextmanager


class TaskWrapper:
    """任务包装器，用于优先级队列"""
    
    def __init__(self, func: Callable, args: tuple, kwargs: dict, task_id: str):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.task_id = task_id
        self.created_at = time.time()
    
    def __lt__(self, other):
        """支持优先级队列比较"""
        if isinstance(other, TaskWrapper):
            return self.created_at < other.created_at
        return NotImplemented
    
    def __eq__(self, other):
        """支持相等比较"""
        if isinstance(other, TaskWrapper):
            return self.task_id == other.task_id
        return NotImplemented
    
    def __hash__(self):
        """支持哈希"""
        return hash(self.task_id)
    
    async def execute(self) -> Any:
        """执行任务"""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(*self.args, **self.kwargs)
        else:
            return self.func(*self.args, **self.kwargs)

# 配置日志
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级枚举"""
    CRITICAL = 1    # 关键任务（用户查询）
    HIGH = 2        # 高优先级（实体关系合并）
    MEDIUM = 3      # 中等优先级（文档处理）
    LOW = 4         # 低优先级（后台清理）
    BACKGROUND = 5  # 后台任务（缓存维护）


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"        # 等待执行
    RUNNING = "running"        # 正在执行
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 执行失败
    CANCELLED = "cancelled"    # 已取消
    TIMEOUT = "timeout"        # 超时


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    task_type: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Any = None


class AsyncTaskManager:
    """
    改进的异步任务管理器
    
    提供了完整的任务生命周期管理，包括优先级调度、错误处理、
    资源管理和并发控制等功能。
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 4,
        max_queue_size: int = 1000,
        default_timeout: float = 300.0,
        cleanup_interval: float = 60.0
    ):
        """
        初始化异步任务管理器
        
        Args:
            max_concurrent_tasks: 最大并发任务数
            max_queue_size: 最大队列大小
            default_timeout: 默认任务超时时间（秒）
            cleanup_interval: 清理间隔时间（秒）
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_queue_size = max_queue_size
        self.default_timeout = default_timeout
        self.cleanup_interval = cleanup_interval
        
        # 任务管理
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._task_info: Dict[str, TaskInfo] = {}
        self._completed_tasks: Dict[str, TaskInfo] = {}
        
        # 并发控制
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._shutdown_event = asyncio.Event()
        
        # 统计信息
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "timeout_tasks": 0
        }
        
        # 后台任务
        self._worker_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # 弱引用集合，用于跟踪活跃的任务
        self._active_tasks: Set[weakref.ref] = set()
        
        logger.info(f"异步任务管理器已初始化，最大并发数: {max_concurrent_tasks}")
    
    async def start(self) -> None:
        """启动任务管理器"""
        if self._worker_task is not None:
            logger.warning("任务管理器已经启动")
            return
        
        logger.info("启动异步任务管理器")
        self._worker_task = asyncio.create_task(self._worker_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self, timeout: float = 30.0) -> None:
        """停止任务管理器"""
        logger.info("停止异步任务管理器")
        
        # 设置停止标志
        self._shutdown_event.set()
        
        # 取消所有运行中的任务
        await self._cancel_all_running_tasks()
        
        # 停止后台任务
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await asyncio.wait_for(self._worker_task, timeout=timeout)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=timeout)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        
        logger.info("异步任务管理器已停止")
    
    async def submit_task(
        self,
        coro: Callable,
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        task_type: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        提交异步任务
        
        Args:
            coro: 协程函数
            task_id: 任务ID（可选，自动生成）
            priority: 任务优先级
            timeout: 任务超时时间
            max_retries: 最大重试次数
            task_type: 任务类型
            metadata: 任务元数据
            **kwargs: 传递给协程函数的参数
        
        Returns:
            str: 任务ID
        
        Raises:
            asyncio.QueueFull: 队列已满
        """
        if task_id is None:
            task_id = f"task_{int(time.time() * 1000000)}_{id(coro)}"
        
        if timeout is None:
            timeout = self.default_timeout
        
        # 创建任务信息
        task_info = TaskInfo(
            task_id=task_id,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            task_type=task_type,
            metadata=metadata or {}
        )
        
        # 创建任务包装器 - 使用可比较的包装器
        task_wrapper = TaskWrapper(coro, (), kwargs, task_id)
        
        # 添加到队列
        try:
            await self._task_queue.put((priority.value, time.time(), task_id, task_wrapper))
            self._task_info[task_id] = task_info
            self._stats["total_tasks"] += 1
            
            logger.debug(f"任务已提交: {task_id}, 优先级: {priority.name}, 类型: {task_type}")
            return task_id
        
        except asyncio.QueueFull:
            logger.error(f"任务队列已满，无法提交任务: {task_id}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消指定任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            bool: 是否成功取消
        """
        # 检查是否在运行中
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            task.cancel()
            
            # 更新任务状态
            if task_id in self._task_info:
                self._task_info[task_id].status = TaskStatus.CANCELLED
                self._task_info[task_id].completed_at = time.time()
            
            logger.info(f"已取消运行中的任务: {task_id}")
            return True
        
        # 检查是否在队列中
        if task_id in self._task_info:
            self._task_info[task_id].status = TaskStatus.CANCELLED
            self._task_info[task_id].completed_at = time.time()
            logger.info(f"已标记队列中的任务为取消: {task_id}")
            return True
        
        logger.warning(f"未找到要取消的任务: {task_id}")
        return False
    
    async def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            Optional[TaskInfo]: 任务信息，如果不存在则返回None
        """
        # 首先检查活跃任务
        if task_id in self._task_info:
            return self._task_info[task_id]
        
        # 然后检查已完成任务
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        
        return None
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> TaskInfo:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 等待超时时间
        
        Returns:
            TaskInfo: 任务信息
        
        Raises:
            asyncio.TimeoutError: 等待超时
            ValueError: 任务不存在
        """
        start_time = time.time()
        
        while True:
            try:
                task_info = await self.get_task_status(task_id)
                if task_info is None:
                    raise ValueError(f"任务不存在: {task_id}")
                
                if task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                    return task_info
                
                if timeout and (time.time() - start_time) > timeout:
                    raise asyncio.TimeoutError(f"等待任务完成超时: {task_id}")
                
                # 使用可取消的睡眠，但捕获取消异常
                try:
                    await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    # 如果等待被取消，检查任务是否已完成
                    final_task_info = await self.get_task_status(task_id)
                    if final_task_info and final_task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                        return final_task_info
                    # 如果任务未完成，将其标记为取消
                    if final_task_info:
                        final_task_info.status = TaskStatus.CANCELLED
                        final_task_info.completed_at = time.time()
                        return final_task_info
                    raise
            
            except asyncio.CancelledError:
                # 处理外层取消
                logger.warning(f"等待任务 {task_id} 被取消")
                task_info = await self.get_task_status(task_id)
                if task_info:
                    task_info.status = TaskStatus.CANCELLED
                    task_info.completed_at = time.time()
                    return task_info
                raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            **self._stats,
            "running_tasks": len(self._running_tasks),
            "queued_tasks": self._task_queue.qsize(),
            "active_tasks": len(self._active_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
    
    async def _worker_loop(self) -> None:
        """工作线程主循环"""
        logger.info("任务工作线程已启动")
        
        while not self._shutdown_event.is_set():
            try:
                # 等待信号量
                try:
                    await self._semaphore.acquire()
                except asyncio.CancelledError:
                    logger.info("工作线程信号量等待被取消")
                    break
                
                try:
                    # 从队列获取任务
                    try:
                        priority, submit_time, task_id, task_wrapper = await asyncio.wait_for(
                            self._task_queue.get(),
                            timeout=1.0
                        )
                    except asyncio.CancelledError:
                        self._semaphore.release()
                        logger.info("工作线程队列等待被取消")
                        break
                    
                    # 检查任务是否已被取消
                    if task_id in self._task_info and self._task_info[task_id].status == TaskStatus.CANCELLED:
                        logger.debug(f"跳过已取消的任务: {task_id}")
                        self._semaphore.release()
                        continue
                    
                    # 创建并启动任务
                    task = asyncio.create_task(self._execute_task(task_id, task_wrapper))
                    self._running_tasks[task_id] = task
                    
                    # 添加弱引用
                    self._active_tasks.add(weakref.ref(task))
                    
                except asyncio.TimeoutError:
                    # 队列为空，释放信号量并继续
                    self._semaphore.release()
                    continue
                
            except asyncio.CancelledError:
                logger.info("工作线程主循环被取消")
                break
            except Exception as e:
                logger.error(f"工作线程异常: {e}")
                logger.error(traceback.format_exc())
                try:
                    await asyncio.sleep(1.0)
                except asyncio.CancelledError:
                    break
        
        logger.info("任务工作线程已停止")
    
    async def _execute_task(self, task_id: str, task_wrapper: Callable) -> None:
        """
        执行单个任务
        
        Args:
            task_id: 任务ID
            task_wrapper: 任务包装器
        """
        task_info = self._task_info.get(task_id)
        if not task_info:
            logger.error(f"任务信息不存在: {task_id}")
            self._semaphore.release()
            return
        
        try:
            # 更新任务状态
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = time.time()
            
            logger.debug(f"开始执行任务: {task_id}")
            
            # 执行任务（带超时）
            if task_info.timeout:
                result = await asyncio.wait_for(task_wrapper.execute(), timeout=task_info.timeout)
            else:
                result = await task_wrapper.execute()
            
            # 保存任务结果
            task_info.result = result
            
            # 任务成功完成
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = time.time()
            self._stats["completed_tasks"] += 1
            
            logger.debug(f"任务执行成功: {task_id}")
            
        except asyncio.CancelledError:
            # 任务被取消
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = time.time()
            self._stats["cancelled_tasks"] += 1
            
            logger.info(f"任务被取消: {task_id}")
            # 不重新抛出CancelledError，让任务正常结束
            
        except asyncio.TimeoutError:
            # 任务超时
            task_info.status = TaskStatus.TIMEOUT
            task_info.completed_at = time.time()
            task_info.error_message = f"任务执行超时 ({task_info.timeout}s)"
            self._stats["timeout_tasks"] += 1
            
            logger.warning(f"任务执行超时: {task_id}")
            
        except Exception as e:
            # 任务执行失败
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = time.time()
            task_info.error_message = str(e)
            task_info.retry_count += 1
            
            logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            logger.error(traceback.format_exc())
            
            # 检查是否需要重试
            if task_info.retry_count < task_info.max_retries:
                logger.info(f"任务将重试: {task_id}, 重试次数: {task_info.retry_count}/{task_info.max_retries}")
                
                # 重新提交任务
                task_info.status = TaskStatus.PENDING
                task_info.started_at = None
                task_info.completed_at = None
                
                try:
                    await self._task_queue.put((
                        task_info.priority.value,
                        time.time(),
                        task_id,
                        task_wrapper
                    ))
                except asyncio.QueueFull:
                    logger.error(f"重试队列已满，任务失败: {task_id}")
                    task_info.status = TaskStatus.FAILED
                    self._stats["failed_tasks"] += 1
            else:
                self._stats["failed_tasks"] += 1
        
        finally:
            # 清理运行中的任务
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            
            # 移动到已完成任务
            if task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                self._completed_tasks[task_id] = task_info
                if task_id in self._task_info:
                    del self._task_info[task_id]
            
            # 释放信号量
            self._semaphore.release()
    
    async def _cleanup_loop(self) -> None:
        """清理循环，定期清理已完成的任务"""
        logger.info("清理任务已启动")
        
        while not self._shutdown_event.is_set():
            try:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                except asyncio.CancelledError:
                    logger.info("清理任务睡眠被取消")
                    break
                
                await self._cleanup_completed_tasks()
                await self._cleanup_weak_references()
                
            except asyncio.CancelledError:
                logger.info("清理任务循环被取消")
                break
            except Exception as e:
                logger.error(f"清理任务异常: {e}")
                logger.error(traceback.format_exc())
                try:
                    await asyncio.sleep(1.0)
                except asyncio.CancelledError:
                    break
        
        logger.info("清理任务已停止")
    
    async def _cleanup_completed_tasks(self, max_age: float = 3600.0) -> None:
        """
        清理过期的已完成任务
        
        Args:
            max_age: 最大保留时间（秒）
        """
        current_time = time.time()
        expired_tasks = []
        
        for task_id, task_info in self._completed_tasks.items():
            if task_info.completed_at and (current_time - task_info.completed_at) > max_age:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del self._completed_tasks[task_id]
        
        if expired_tasks:
            logger.debug(f"清理了 {len(expired_tasks)} 个过期任务")
    
    async def _cleanup_weak_references(self) -> None:
        """清理失效的弱引用"""
        dead_refs = [ref for ref in self._active_tasks if ref() is None]
        for ref in dead_refs:
            self._active_tasks.discard(ref)
        
        if dead_refs:
            logger.debug(f"清理了 {len(dead_refs)} 个失效的弱引用")
    
    async def _cancel_all_running_tasks(self) -> None:
        """取消所有运行中的任务"""
        if not self._running_tasks:
            return
        
        logger.info(f"取消 {len(self._running_tasks)} 个运行中的任务")
        
        # 取消所有任务
        for task_id, task in self._running_tasks.items():
            task.cancel()
        
        # 等待所有任务完成取消
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks.values(), return_exceptions=True)
    
    @asynccontextmanager
    async def task_context(self):
        """任务管理器上下文管理器"""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()


# 全局任务管理器实例
_global_task_manager: Optional[AsyncTaskManager] = None


async def get_global_task_manager(
    max_concurrent_tasks: int = 4,
    **kwargs
) -> AsyncTaskManager:
    """
    获取全局任务管理器实例
    
    Args:
        max_concurrent_tasks: 最大并发任务数
        **kwargs: 其他初始化参数
    
    Returns:
        AsyncTaskManager: 全局任务管理器实例
    """
    global _global_task_manager
    
    if _global_task_manager is None:
        _global_task_manager = AsyncTaskManager(
            max_concurrent_tasks=max_concurrent_tasks,
            **kwargs
        )
        await _global_task_manager.start()
    
    return _global_task_manager


async def shutdown_global_task_manager() -> None:
    """关闭全局任务管理器"""
    global _global_task_manager
    
    if _global_task_manager is not None:
        await _global_task_manager.stop()
        _global_task_manager = None


if __name__ == "__main__":
    # 示例用法
    async def example_task(name: str, duration: float = 1.0) -> str:
        """示例任务函数"""
        logger.info(f"开始执行任务: {name}")
        await asyncio.sleep(duration)
        logger.info(f"任务完成: {name}")
        return f"任务 {name} 已完成"
    
    async def main():
        """主函数示例"""
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 创建任务管理器
        async with AsyncTaskManager(max_concurrent_tasks=2).task_context() as manager:
            # 提交多个任务
            task_ids = []
            for i in range(5):
                task_id = await manager.submit_task(
                    example_task,
                    task_type="example",
                    priority=TaskPriority.MEDIUM,
                    name=f"task_{i}",
                    duration=2.0
                )
                task_ids.append(task_id)
            
            # 等待所有任务完成
            for task_id in task_ids:
                task_info = await manager.wait_for_task(task_id)
                logger.info(f"任务 {task_id} 状态: {task_info.status.value}")
            
            # 打印统计信息
            stats = await manager.get_statistics()
            logger.info(f"统计信息: {stats}")
    
    # 运行示例
    asyncio.run(main())