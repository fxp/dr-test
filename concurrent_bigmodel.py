#!/usr/bin/env python3
"""并发执行BigModel分析的脚本

这个脚本基于bigmodel_loop.py，添加了并发执行能力：
- 支持N个并发worker同时处理不同的话题
- 提供多种并发模式：multiprocessing, threading, asyncio
- 支持批量处理和实时处理模式
- 完整的错误处理和进度监控
- 兼容LangSmith追踪

使用示例:
    # 使用4个进程并发处理
    python concurrent_bigmodel.py --topics "AI技术" "新能源" "医疗科技" "智能制造" --concurrency 4 --mode multiprocess

    # 使用8个线程并发处理
    python concurrent_bigmodel.py --topics "AI技术" "新能源" --concurrency 8 --mode threading --iterations 3

    # 使用异步模式处理
    python concurrent_bigmodel.py --topics "AI技术" "新能源" --concurrency 4 --mode asyncio --batch-size 10
"""

import argparse
import asyncio
import json
import logging
import multiprocessing as mp
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Union, Iterator
from queue import Queue
import signal

from dotenv import load_dotenv

# 导入原始模块的必要组件
from bigmodel_loop import (
    BigModelClient, 
    build_analysis_prompt, 
    DEFAULT_CHAT_MODEL, 
    DEFAULT_TOOL_MODEL
)

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(processName)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('concurrent_bigmodel.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """单个任务的结果"""
    topic: str
    success: bool
    analysis: Optional[str] = None
    search_results_count: int = 0
    error_message: Optional[str] = None
    execution_time: float = 0.0
    worker_id: Optional[str] = None
    timestamp: str = ""


@dataclass 
class ConcurrentConfig:
    """并发执行配置"""
    concurrency: int = 4
    mode: str = "multiprocessing"  # multiprocessing, threading, asyncio
    batch_size: int = 0  # 0表示不使用批处理
    timeout: int = 120  # 单个任务超时时间（秒）
    max_retries: int = 2  # 最大重试次数
    delay_between_tasks: float = 0.5  # 任务间延迟
    progress_interval: int = 5  # 进度报告间隔（秒）


class TaskWorker:
    """任务工作器 - 处理单个分析任务"""
    
    def __init__(self, api_key: str, chat_model: str, tool_model: str, worker_id: str):
        self.api_key = api_key
        self.chat_model = chat_model 
        self.tool_model = tool_model
        self.worker_id = worker_id
        self._client = None
    
    @property
    def client(self) -> BigModelClient:
        """延迟初始化客户端（支持multiprocessing）"""
        if self._client is None:
            self._client = BigModelClient(api_key=self.api_key)
        return self._client
    
    def process_topic(self, topic: str) -> TaskResult:
        """处理单个话题分析"""
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            logger.info(f"Worker {self.worker_id} 开始处理话题: {topic}")
            
            # 搜索阶段
            search_results = self.client.web_search(topic, model=self.tool_model)
            
            # 打印 Worker 搜索结果摘要
            print(f"🔍 [{self.worker_id}] 搜索完成: '{topic}' -> {len(search_results)} 个结果")
            if search_results:
                # 显示第一个结果的标题作为验证
                first_result = search_results[0]
                title = first_result.get('title', '无标题')[:40]
                print(f"📄 [{self.worker_id}] 首个结果: {title}...")
            
            # 构建分析prompt
            prompt = build_analysis_prompt(topic, search_results)
            messages = [
                {
                    "role": "system",
                    "content": "你是专业的中文商业分析顾问，回答时请使用简洁的中文段落并分点列出结论。",
                },
                {
                    "role": "user", 
                    "content": prompt,
                },
            ]
            
            # 分析阶段
            analysis = self.client.chat_completion(messages, model=self.chat_model)
            
            execution_time = time.time() - start_time
            
            logger.info(f"Worker {self.worker_id} 完成话题 '{topic}' (耗时: {execution_time:.2f}s)")
            
            return TaskResult(
                topic=topic,
                success=True,
                analysis=analysis,
                search_results_count=len(search_results),
                execution_time=execution_time,
                worker_id=self.worker_id,
                timestamp=timestamp
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"处理话题 '{topic}' 时出错: {str(e)}"
            logger.error(f"Worker {self.worker_id}: {error_msg}")
            
            return TaskResult(
                topic=topic,
                success=False,
                error_message=error_msg,
                execution_time=execution_time,
                worker_id=self.worker_id,
                timestamp=timestamp
            )


def process_topic_multiprocessing(args_tuple) -> TaskResult:
    """多进程处理函数 - 全局函数以支持pickle"""
    api_key, chat_model, tool_model, worker_id, topic = args_tuple
    worker = TaskWorker(api_key, chat_model, tool_model, worker_id)
    return worker.process_topic(topic)


class ConcurrentBigModelExecutor:
    """并发BigModel执行器"""
    
    def __init__(self, config: ConcurrentConfig, api_key: str, 
                 chat_model: str = DEFAULT_CHAT_MODEL, 
                 tool_model: str = DEFAULT_TOOL_MODEL):
        self.config = config
        self.api_key = api_key
        self.chat_model = chat_model
        self.tool_model = tool_model
        self.results: List[TaskResult] = []
        self._stop_event = threading.Event()
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器 - 优雅停止"""
        logger.info(f"接收到信号 {signum}, 正在优雅停止...")
        self._stop_event.set()
    
    def execute_concurrent(self, topics: List[str], iterations: int = 1) -> List[TaskResult]:
        """执行并发分析"""
        all_results = []
        
        # 处理iterations=0的情况（无限执行）
        if iterations == 0:
            logger.info("启动无限执行模式 (iterations=0)")
            iteration = 1
            while not self._stop_event.is_set():
                logger.info(f"开始第 {iteration} 轮并发分析 (无限模式)")
                logger.info(f"话题数量: {len(topics)}, 并发度: {self.config.concurrency}, 模式: {self.config.mode}")
                
                # 执行本轮分析
                if self.config.mode == "multiprocessing":
                    results = self._execute_multiprocessing(topics, iteration)
                elif self.config.mode == "threading":
                    results = self._execute_threading(topics, iteration)
                elif self.config.mode == "asyncio":
                    results = self._execute_asyncio(topics, iteration)
                else:
                    raise ValueError(f"不支持的并发模式: {self.config.mode}")
                
                all_results.extend(results)
                
                # 报告本轮结果
                self._report_iteration_results(results, iteration)
                
                iteration += 1
                
                # 轮次间延迟
                if not self._stop_event.is_set():
                    logger.info(f"等待 {self.config.delay_between_tasks} 秒后开始下一轮...")
                    time.sleep(self.config.delay_between_tasks)
        else:
            # 正常的有限次数执行
            for iteration in range(1, iterations + 1):
                if self._stop_event.is_set():
                    logger.info("接收到停止信号，终止执行")
                    break
                    
                logger.info(f"开始第 {iteration}/{iterations} 轮并发分析")
                logger.info(f"话题数量: {len(topics)}, 并发度: {self.config.concurrency}, 模式: {self.config.mode}")
                
                # 根据模式选择执行方法
                if self.config.mode == "multiprocessing":
                    results = self._execute_multiprocessing(topics, iteration)
                elif self.config.mode == "threading":
                    results = self._execute_threading(topics, iteration)
                elif self.config.mode == "asyncio":
                    results = self._execute_asyncio(topics, iteration)
                else:
                    raise ValueError(f"不支持的并发模式: {self.config.mode}")
                
                all_results.extend(results)
                
                # 报告本轮结果
                self._report_iteration_results(results, iteration)
                
                # 轮次间延迟
                if iteration < iterations and not self._stop_event.is_set():
                    logger.info(f"等待 {self.config.delay_between_tasks} 秒后开始下一轮...")
                    time.sleep(self.config.delay_between_tasks)
        
        return all_results
    
    def _execute_multiprocessing(self, topics: List[str], iteration: int) -> List[TaskResult]:
        """多进程执行"""
        logger.info(f"使用多进程模式，进程数: {self.config.concurrency}")
        
        # 准备任务参数
        task_args = [
            (self.api_key, self.chat_model, self.tool_model, f"P{i%self.config.concurrency}-{iteration}", topic)
            for i, topic in enumerate(topics)
        ]
        
        results = []
        
        with ProcessPoolExecutor(max_workers=self.config.concurrency) as executor:
            # 提交所有任务
            future_to_topic = {
                executor.submit(process_topic_multiprocessing, args): args[4] 
                for args in task_args
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_topic, timeout=self.config.timeout * len(topics)):
                try:
                    result = future.result(timeout=self.config.timeout)
                    results.append(result)
                except Exception as e:
                    topic = future_to_topic[future]
                    logger.error(f"处理话题 '{topic}' 时出错: {e}")
                    results.append(TaskResult(
                        topic=topic,
                        success=False,
                        error_message=str(e),
                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                
                # 在收集结果后检查停止信号
                if self._stop_event.is_set():
                    logger.info("检测到停止信号，终止后续任务收集")
                    break
        
        return results
    
    def _execute_threading(self, topics: List[str], iteration: int) -> List[TaskResult]:
        """多线程执行"""
        logger.info(f"使用多线程模式，线程数: {self.config.concurrency}")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.concurrency) as executor:
            # 创建workers并提交任务
            future_to_topic = {}
            
            for i, topic in enumerate(topics):
                if self._stop_event.is_set():
                    break
                    
                worker_id = f"T{i%self.config.concurrency}-{iteration}"
                worker = TaskWorker(self.api_key, self.chat_model, self.tool_model, worker_id)
                future = executor.submit(worker.process_topic, topic)
                future_to_topic[future] = topic
            
            # 处理完成的任务
            for future in as_completed(future_to_topic, timeout=self.config.timeout * len(topics)):
                try:
                    result = future.result(timeout=self.config.timeout)
                    results.append(result)
                except Exception as e:
                    topic = future_to_topic[future]
                    logger.error(f"处理话题 '{topic}' 时出错: {e}")
                    results.append(TaskResult(
                        topic=topic,
                        success=False,
                        error_message=str(e),
                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                
                # 在收集结果后检查停止信号
                if self._stop_event.is_set():
                    logger.info("检测到停止信号，终止后续任务收集")
                    break
        
        return results
    
    def _execute_asyncio(self, topics: List[str], iteration: int) -> List[TaskResult]:
        """异步执行"""
        logger.info(f"使用异步模式，并发度: {self.config.concurrency}")
        
        # 在新的事件循环中运行异步任务
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._async_execute_topics(topics, iteration))
    
    async def _async_execute_topics(self, topics: List[str], iteration: int) -> List[TaskResult]:
        """异步执行话题分析"""
        semaphore = asyncio.Semaphore(self.config.concurrency)
        
        async def process_topic_async(topic: str, worker_id: str) -> TaskResult:
            async with semaphore:
                # 在线程池中执行同步的API调用
                loop = asyncio.get_event_loop()
                worker = TaskWorker(self.api_key, self.chat_model, self.tool_model, worker_id)
                result = await loop.run_in_executor(None, worker.process_topic, topic)
                return result
        
        # 创建所有异步任务
        tasks = [
            process_topic_async(topic, f"A{i%self.config.concurrency}-{iteration}")
            for i, topic in enumerate(topics)
        ]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                topic = topics[i]
                logger.error(f"异步处理话题 '{topic}' 时出错: {result}")
                processed_results.append(TaskResult(
                    topic=topic,
                    success=False,
                    error_message=str(result),
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _report_iteration_results(self, results: List[TaskResult], iteration: int):
        """报告单轮结果"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_time = sum(r.execution_time for r in results)
        avg_time = total_time / len(results) if results else 0
        
        logger.info(f"第 {iteration} 轮完成:")
        logger.info(f"  总任务数: {len(results)}")
        logger.info(f"  成功: {len(successful)}")
        logger.info(f"  失败: {len(failed)}")
        logger.info(f"  总耗时: {total_time:.2f}s")
        logger.info(f"  平均耗时: {avg_time:.2f}s")
        
        if failed:
            logger.warning("失败的话题:")
            for result in failed:
                logger.warning(f"  - {result.topic}: {result.error_message}")
    
    def save_results(self, results: List[TaskResult], output_file: str = None):
        """保存结果到文件"""
        if not output_file:
            output_file = f"concurrent_results_{int(time.time())}.json"
        
        # 转换为可序列化的格式
        serializable_results = [asdict(result) for result in results]
        
        # 添加汇总信息
        summary = {
            "total_tasks": len(results),
            "successful_tasks": len([r for r in results if r.success]),
            "failed_tasks": len([r for r in results if not r.success]),
            "total_execution_time": sum(r.execution_time for r in results),
            "average_execution_time": sum(r.execution_time for r in results) / len(results) if results else 0,
            "config": asdict(self.config),
            "models": {
                "chat_model": self.chat_model,
                "tool_model": self.tool_model
            }
        }
        
        output_data = {
            "summary": summary,
            "results": serializable_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存到: {output_file}")
    
    def print_results_summary(self, results: List[TaskResult]):
        """打印结果摘要"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print("\n" + "="*60)
        print("并发执行结果摘要")
        print("="*60)
        print(f"总任务数: {len(results)}")
        
        if len(results) > 0:
            print(f"成功: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
            print(f"失败: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        else:
            print("成功: 0 (0.0%)")
            print("失败: 0 (0.0%)")
        
        if results:
            total_time = sum(r.execution_time for r in results)
            print(f"总执行时间: {total_time:.2f}s")
            print(f"平均执行时间: {total_time/len(results):.2f}s")
        
        # 按worker统计
        worker_stats = {}
        for result in results:
            if result.worker_id:
                if result.worker_id not in worker_stats:
                    worker_stats[result.worker_id] = {"success": 0, "failed": 0, "time": 0}
                
                if result.success:
                    worker_stats[result.worker_id]["success"] += 1
                else:
                    worker_stats[result.worker_id]["failed"] += 1
                worker_stats[result.worker_id]["time"] += result.execution_time
        
        if worker_stats:
            print(f"\nWorker 统计:")
            for worker_id, stats in sorted(worker_stats.items()):
                print(f"  {worker_id}: {stats['success']}成功/{stats['failed']}失败, 耗时:{stats['time']:.1f}s")
        
        # 显示失败的任务
        if failed:
            print(f"\n失败的任务 ({len(failed)}):")
            for result in failed:
                print(f"  - {result.topic}: {result.error_message}")
        
        # 显示成功任务的样例
        if successful:
            print(f"\n成功任务样例:")
            sample = successful[0]
            print(f"  话题: {sample.topic}")
            print(f"  搜索结果数: {sample.search_results_count}")
            print(f"  分析长度: {len(sample.analysis or '') if sample.analysis else 0} 字符")
            print(f"  执行时间: {sample.execution_time:.2f}s")
            if sample.analysis:
                preview = sample.analysis[:200] + "..." if len(sample.analysis) > 200 else sample.analysis
                print(f"  分析预览: {preview}")


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="并发执行BigModel分析")
    
    # 基本参数
    parser.add_argument(
        "--api-key",
        default=os.getenv("BIGMODEL_API_KEY"),
        help="BigModel API key"
    )
    parser.add_argument(
        "--topics", 
        nargs="*",
        default=["人工智能热点", "新能源产业", "医疗科技创新", "智能制造", "金融科技"],
        help="要分析的话题列表"
    )
    parser.add_argument(
        "--iterations",
        type=int, 
        default=1,
        help="执行轮数 (0=无限执行，直到手动停止)"
    )
    
    # 并发参数
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=4, 
        help="并发数量 (进程/线程数)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["multiprocessing", "threading", "asyncio"],
        default="multiprocessing",
        help="并发模式"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=0,
        help="批处理大小 (0=不使用批处理)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=120,
        help="单任务超时时间(秒)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="最大重试次数"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="任务间延迟(秒)"
    )
    
    # 模型参数
    parser.add_argument(
        "--chat-model",
        default=DEFAULT_CHAT_MODEL,
        help="聊天模型名称"
    )
    parser.add_argument(
        "--tool-model", 
        default=DEFAULT_TOOL_MODEL,
        help="工具模型名称"
    )
    
    # 输出参数
    parser.add_argument(
        "--output", "-o",
        help="结果输出文件路径"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，减少日志输出"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 配置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # 验证API key
    if not args.api_key:
        logger.error("缺少 BIGMODEL_API_KEY，请通过 --api-key 参数或环境变量提供")
        return 1
    
    # 创建并发配置
    config = ConcurrentConfig(
        concurrency=args.concurrency,
        mode=args.mode,
        batch_size=args.batch_size,
        timeout=args.timeout,
        max_retries=args.max_retries,
        delay_between_tasks=args.delay
    )
    
    # 创建执行器
    executor = ConcurrentBigModelExecutor(
        config=config,
        api_key=args.api_key,
        chat_model=args.chat_model,
        tool_model=args.tool_model
    )
    
    try:
        logger.info("开始并发执行BigModel分析")
        logger.info(f"配置: {asdict(config)}")
        
        # 执行分析
        start_time = time.time()
        results = executor.execute_concurrent(args.topics, args.iterations)
        total_time = time.time() - start_time
        
        logger.info(f"所有任务执行完成，总耗时: {total_time:.2f}s")
        
        # 保存结果
        if args.output:
            executor.save_results(results, args.output)
        else:
            executor.save_results(results)
        
        # 打印摘要
        if not args.quiet:
            executor.print_results_summary(results)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        return 1
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # 支持多进程
    mp.freeze_support()
    sys.exit(main())