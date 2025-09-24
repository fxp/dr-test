"""Looping BigModel web search + chat analysis script.

This script demonstrates how to continuously call BigModel's Web Search tool
API together with the chat completion API to analyse a rotating list of topics.
The implementation follows the public documentation:
  - Web Search: https://docs.bigmodel.cn/api-reference/%E5%B7%A5%E5%85%B7-api/%E7%BD%91%E7%BB%9C%E6%90%9C%E7%B4%A2
  - Chat completion: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8

Set the API key in the BIGMODEL_API_KEY environment variable or pass it through
command-line arguments. For quick experiments the key provided by the user can
be used directly: ``b8ae5075e7fa49c0bf6f248b38de2152.8DCFTJBF5qKJH3KL``.

LangSmith Integration:
  Set LANGSMITH_API_KEY and LANGSMITH_PROJECT environment variables for tracing.
  
Usage example::

    export BIGMODEL_API_KEY="<your_api_key>"
    export LANGSMITH_API_KEY="<your_langsmith_key>"
    export LANGSMITH_PROJECT="bigmodel-analysis"
    python bigmodel_loop.py --topics "自动驾驶" "智能制造" --iterations 1

"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from typing import Iterable, List, Mapping, Optional, Any, Dict

import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Set up LangSmith environment variables
langsmith_key = os.getenv("LANGSMITH_API_KEY")
langsmith_project = os.getenv("LANGSMITH_PROJECT", "bigmodel")
langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

if langsmith_key:
    # Set LangChain environment variables for LangSmith
    os.environ["LANGCHAIN_API_KEY"] = langsmith_key
    os.environ["LANGCHAIN_PROJECT"] = langsmith_project
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = langsmith_endpoint

# LangSmith imports and setup
try:
    from langsmith import Client, traceable
    from langsmith.wrappers import wrap_openai
    LANGSMITH_AVAILABLE = True
    
    # Initialize LangSmith client if API key is available
    if langsmith_key:
        langsmith_client = Client(
            api_key=langsmith_key,
            api_url=langsmith_endpoint
        )
        print(f"✅ LangSmith initialized for project: {langsmith_project}")
        print(f"📊 Tracing URL: https://smith.langchain.com/projects/{langsmith_project}")
    else:
        langsmith_client = None
        print("⚠️  LangSmith API key not found, running without tracing")
        
except ImportError:
    LANGSMITH_AVAILABLE = False
    langsmith_client = None
    print("❌ LangSmith not available. Install with: pip install langsmith")
    
    # 创建空装饰器作为回退
    def traceable(name=None, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def wrap_openai(client):
        return client

# API Endpoints
WEB_SEARCH_URL = "https://open.bigmodel.cn/api/paas/v4/web_search"
BIGMODEL_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# Default models
DEFAULT_CHAT_MODEL = os.getenv("DEFAULT_CHAT_MODEL", "glm-4.5-aq")
DEFAULT_TOOL_MODEL = os.getenv("DEFAULT_TOOL_MODEL", "glm-4.5-aq")


class BigModelClient:
    """BigModel API client using OpenAI SDK with LangSmith tracing."""

    def __init__(self, api_key: str, timeout: int = 60) -> None:
        if not api_key:
            raise ValueError(
                "BigModel API key is missing. Provide it through --api-key or the BIGMODEL_API_KEY environment variable."
            )

        # Initialize OpenAI client for BigModel API
        self._openai_client = OpenAI(
            api_key=api_key,
            base_url=BIGMODEL_BASE_URL,
            timeout=timeout
        )
        
        # Wrap with LangSmith tracing if available
        if LANGSMITH_AVAILABLE and langsmith_client:
            self._openai_client = wrap_openai(self._openai_client)
            
        # Keep requests session for web search (non-OpenAI endpoint)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        self._timeout = timeout

    def web_search(self, query: str, *, model: str = DEFAULT_TOOL_MODEL, top_k: int = 5) -> List[Mapping[str, str]]:
        """Perform a web search using BigModel's tool API with LangSmith tracing."""
        
        # Use manual tracing for web search since it's not covered by OpenAI wrapper
        if LANGSMITH_AVAILABLE and langsmith_client:
            return self._traced_web_search(query, model=model, top_k=top_k)
        else:
            return self._web_search_impl(query, model=model, top_k=top_k)
    
    def _traced_web_search(self, query: str, *, model: str = DEFAULT_TOOL_MODEL, top_k: int = 5) -> List[Mapping[str, str]]:
        """Web search with LangSmith tracing."""
        from langsmith import traceable
        
        @traceable(
            name="web_search",
            tags=["web_search", "bigmodel", "search"],
            metadata={
                "search_engine": os.getenv("SEARCH_ENGINE", "search-prime-aqdr"),
                "content_size": os.getenv("SEARCH_CONTENT_SIZE", "medium")
            }
        )
        def traced_search(query: str, model: str, top_k: int) -> Dict[str, Any]:
            results = self._web_search_impl(query, model=model, top_k=top_k)
            return {
                "query": query,
                "model": model,
                "top_k": top_k,
                "results_count": len(results),
                "results": results
            }
        
        traced_result = traced_search(query, model, top_k)
        return traced_result["results"]
    
    def _web_search_impl(self, query: str, *, model: str = DEFAULT_TOOL_MODEL, top_k: int = 5) -> List[Mapping[str, str]]:
        """Internal web search implementation."""
        
        payload = {
            "search_query": query,
            "search_engine": os.getenv("SEARCH_ENGINE", "search-prime-aqdr"),
            "search_intent": False,
            "count": min(top_k, 50),
            "content_size": os.getenv("SEARCH_CONTENT_SIZE", "medium"),
        }

        start_time = time.time()
        response = self._session.post(WEB_SEARCH_URL, json=payload, timeout=self._timeout)
        elapsed_time = time.time() - start_time
        print(f"[Web Search] 耗时: {elapsed_time:.2f}秒")
        
        self._ensure_success(response, "web search")
        return self._normalize_search_results(response.json())

    @traceable(name="chat_completion")
    def chat_completion(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        model: str = DEFAULT_CHAT_MODEL,
        temperature: float = 0.3,
    ) -> str:
        """Call the chat completion API using OpenAI SDK and return the assistant's reply."""

        start_time = time.time()
        
        try:
            # Convert messages to the format expected by OpenAI SDK
            formatted_messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in messages
            ]
            
            # Call OpenAI API (BigModel compatible)
            response = self._openai_client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature
            )
            
            elapsed_time = time.time() - start_time
            print(f"[Chat Completion] 耗时: {elapsed_time:.2f}秒")
            
            # Extract content from response
            if not response.choices:
                raise RuntimeError(f"No choices in chat response")
                
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError(f"No content in chat response")
                
            return content
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[Chat Completion] 错误 (耗时: {elapsed_time:.2f}秒): {e}")
            raise RuntimeError(f"Chat completion failed: {e}") from e

    def _ensure_success(self, response: requests.Response, context: str) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:  # pragma: no cover - network error path
            detail: Optional[str] = None
            try:
                detail = json.dumps(response.json(), ensure_ascii=False)
            except Exception:
                detail = response.text
            raise RuntimeError(f"BigModel {context} request failed: {detail}") from exc

    @staticmethod
    def _normalize_search_results(payload: Mapping[str, object]) -> List[Mapping[str, str]]:
        """Extract a list of search results from the API response.

        The exact response schema may evolve. This helper aims to support the
        documented format while gracefully degrading if fields are renamed by
        falling back to raw payloads.
        """

        results: List[Mapping[str, str]] = []
        
        # 新的响应格式: {"search_result": [...]}
        search_result = payload.get("search_result", [])
        
        if isinstance(search_result, list):
            for item in search_result:
                if not isinstance(item, Mapping):
                    continue
                results.append(
                    {
                        "title": str(item.get("title") or ""),
                        "url": str(item.get("link") or ""),  # API 中使用 "link"
                        "summary": str(item.get("content") or ""),  # API 中使用 "content"
                    }
                )
        else:
            # Fallback: return the entire payload for debugging/inspection.
            results.append(
                {
                    "title": "Raw response",
                    "url": "",
                    "summary": json.dumps(payload, ensure_ascii=False),
                }
            )

        return results


def build_analysis_prompt(topic: str, search_results: List[Mapping[str, str]]) -> str:
    """Construct the user prompt for the chat model based on search results."""

    formatted_results = []
    for idx, result in enumerate(search_results, start=1):
        block = textwrap.dedent(
            f"""
            {idx}. 标题: {result.get('title', '').strip()}
               链接: {result.get('url', '').strip()}
               摘要: {result.get('summary', '').strip()}
            """
        ).strip()
        formatted_results.append(block)

    joined_results = "\n\n".join(formatted_results) if formatted_results else "(未获取到搜索结果)"

    return textwrap.dedent(
        f"""
        请你扮演行业分析顾问，结合以下关于“{topic}”的最新网页搜索结果，
        输出一段结构化的分析，至少包含以下内容：
        1. 该话题的最新动态；
        2. 潜在的市场机会或风险；
        3. 后续建议或关注点。

        搜索结果：
        {joined_results}
        """
    ).strip()


def cycle_topics(
    client: BigModelClient,
    topics: Iterable[str],
    *,
    iterations: int,
    delay: float,
    chat_model: str,
    tool_model: str,
) -> None:
    """Continuously loop over topics, performing search + chat analysis with separate tracing for each iteration."""

    topics = list(topics)
    if not topics:
        raise ValueError("At least one topic must be provided")

    for iteration in range(1, iterations + 1 if iterations > 0 else sys.maxsize):
        print(f"\n===== 第 {iteration} 轮分析 =====")
        
        # 每个 iteration 都作为独立的 trace
        if LANGSMITH_AVAILABLE and langsmith_client:
            _run_independent_iteration(client, topics, iteration, chat_model, tool_model, delay)
        else:
            _run_iteration_without_tracing(client, topics, iteration, chat_model, tool_model, delay)

        if iterations <= 0:
            time.sleep(delay)


def _run_independent_iteration(client, topics, iteration, chat_model, tool_model, delay):
    """Run iteration as independent trace in LangSmith."""
    @traceable(
        name=f"iteration_{iteration}",
        tags=["iteration", "bigmodel", f"round_{iteration}"],
        metadata={
            "iteration_number": iteration,
            "topics_count": len(topics),
            "topics": topics,
            "chat_model": chat_model,
            "tool_model": tool_model,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    def independent_iteration():
        """Execute one complete iteration as an independent trace."""
        results = []
        for i, topic in enumerate(topics, 1):
            print(f"\n[{i}/{len(topics)}] 处理话题: {topic}")
            result = _analyze_single_topic(client, topic, chat_model, tool_model)
            results.append(result)
            
            # 在同一个 iteration 内的话题之间的延迟
            if i < len(topics):  # 不在最后一个话题后延迟
                time.sleep(delay)
                
        return {
            "iteration": iteration,
            "completed_topics": len(results),
            "total_time": sum(r.get("total_time", 0) for r in results),
            "results_summary": [
                {
                    "topic": r["topic"],
                    "search_results": r["search_results_count"],
                    "analysis_length": r["analysis_length"]
                } for r in results
            ]
        }
    
    return independent_iteration()


def _run_iteration_without_tracing(client, topics, iteration, chat_model, tool_model, delay):
    """Run iteration without tracing."""
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{len(topics)}] 处理话题: {topic}")
        _analyze_single_topic(client, topic, chat_model, tool_model)
        
        if i < len(topics):  # 不在最后一个话题后延迟
            time.sleep(delay)


@traceable(
    name="topic_analysis",
    tags=["topic", "analysis", "bigmodel"]
)
def _analyze_single_topic(client, topic, chat_model, tool_model):
    """Analyze a single topic with full tracing."""
    start_time = time.time()
    print(f"\n--- 话题: {topic} ---")
    
    # Search phase
    search_start = time.time()
    search_results = client.web_search(topic, model=tool_model)
    search_time = time.time() - search_start
    
    # Prompt construction
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
    
    # Analysis phase
    chat_start = time.time()
    analysis = client.chat_completion(messages, model=chat_model)
    chat_time = time.time() - chat_start
    
    print(analysis)
    
    total_time = time.time() - start_time
    
    return {
        "topic": topic,
        "search_results_count": len(search_results),
        "analysis_length": len(analysis),
        "search_time": search_time,
        "chat_time": chat_time,
        "total_time": total_time,
        "models": {
            "chat": chat_model,
            "tool": tool_model
        }
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Loop BigModel web search and chat analysis calls")
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=os.getenv("BIGMODEL_API_KEY"),
        help="BigModel API key. Defaults to BIGMODEL_API_KEY environment variable.",
    )
    parser.add_argument(
        "--topics",
        nargs="*",
        default=["人工智能热点", "新能源产业", "医疗科技创新"],
        help="Topics to analyse in each iteration.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of analysis cycles. Use a non-positive value to loop forever.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Delay in seconds between requests (basic rate limiting).",
    )
    parser.add_argument(
        "--chat-model",
        default=DEFAULT_CHAT_MODEL,
        help="Chat completion model name.",
    )
    parser.add_argument(
        "--tool-model",
        default=DEFAULT_TOOL_MODEL,
        help="Tool (web search) model name.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    try:
        client = BigModelClient(api_key=args.api_key)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        cycle_topics(
            client,
            topics=args.topics,
            iterations=args.iterations,
            delay=args.delay,
            chat_model=args.chat_model,
            tool_model=args.tool_model,
        )
    except Exception as exc:  # pragma: no cover - runtime failure path
        print(f"Error during analysis loop: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
