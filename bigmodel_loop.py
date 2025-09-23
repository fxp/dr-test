"""Looping BigModel web search + chat analysis script.

This script demonstrates how to continuously call BigModel's Web Search tool
API together with the chat completion API to analyse a rotating list of topics.
The implementation follows the public documentation:
  - Web Search: https://docs.bigmodel.cn/api-reference/%E5%B7%A5%E5%85%B7-api/%E7%BD%91%E7%BB%9C%E6%90%9C%E7%B4%A2
  - Chat completion: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8

Set the API key in the BIGMODEL_API_KEY environment variable or pass it through
command-line arguments. For quick experiments the key provided by the user can
be used directly: ``b8ae5075e7fa49c0bf6f248b38de2152.8DCFTJBF5qKJH3KL``.

Usage example::

    export BIGMODEL_API_KEY="<your_api_key>"
    python bigmodel_loop.py --topics "自动驾驶" "智能制造" --iterations 1

"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from typing import Iterable, List, Mapping, Optional

import requests

WEB_SEARCH_URL = "https://open.bigmodel.cn/api/paas/v4/tools/web-search"
CHAT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

DEFAULT_CHAT_MODEL = "glm-4"
DEFAULT_TOOL_MODEL = "glm-4"


class BigModelClient:
    """Simple BigModel API client handling authentication and requests."""

    def __init__(self, api_key: str, timeout: int = 60) -> None:
        if not api_key:
            raise ValueError(
                "BigModel API key is missing. Provide it through --api-key or the BIGMODEL_API_KEY environment variable."
            )

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        self._timeout = timeout

    def web_search(self, query: str, *, model: str = DEFAULT_TOOL_MODEL, top_k: int = 5) -> List[Mapping[str, str]]:
        """Perform a web search using BigModel's tool API.

        Returns a list of search result dictionaries containing ``title``,
        ``url`` and ``summary`` fields when available.
        """

        payload = {
            "model": model,
            "input": {
                "query": query,
                "top_k": top_k,
                "summary": True,
            },
        }

        response = self._session.post(WEB_SEARCH_URL, json=payload, timeout=self._timeout)
        self._ensure_success(response, "web search")
        return self._normalize_search_results(response.json())

    def chat_completion(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        model: str = DEFAULT_CHAT_MODEL,
        temperature: float = 0.3,
    ) -> str:
        """Call the chat completion API and return the assistant's reply."""

        payload = {
            "model": model,
            "temperature": temperature,
            "messages": list(messages),
        }

        response = self._session.post(CHAT_URL, json=payload, timeout=self._timeout)
        self._ensure_success(response, "chat completion")
        data = response.json()

        # The response format follows the OpenAI compatible schema used by BigModel.
        choices = data.get("choices")
        if not choices:
            raise RuntimeError(f"Unexpected chat response payload: {json.dumps(data, ensure_ascii=False)}")

        content = choices[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError(f"Chat response does not contain assistant content: {json.dumps(data, ensure_ascii=False)}")

        return content

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

        # Common response pattern::
        # {
        #   "data": {
        #       "records": [
        #           {"title": "...", "url": "...", "summary": "..."},
        #           ...
        #       ]
        #   }
        # }

        candidates: object = payload
        if isinstance(payload, Mapping):
            if "data" in payload:
                candidates = payload["data"]
            if isinstance(candidates, Mapping) and "records" in candidates:
                candidates = candidates["records"]

        results: List[Mapping[str, str]] = []
        if isinstance(candidates, list):
            for item in candidates:
                if not isinstance(item, Mapping):
                    continue
                results.append(
                    {
                        "title": str(item.get("title") or item.get("name") or ""),
                        "url": str(item.get("url") or item.get("link") or ""),
                        "summary": str(
                            item.get("summary")
                            or item.get("snippet")
                            or item.get("content")
                            or ""
                        ),
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
    """Continuously loop over topics, performing search + chat analysis."""

    topics = list(topics)
    if not topics:
        raise ValueError("At least one topic must be provided")

    for iteration in range(1, iterations + 1 if iterations > 0 else sys.maxsize):
        print(f"\n===== 第 {iteration} 轮分析 =====")
        for topic in topics:
            print(f"\n--- 话题: {topic} ---")
            search_results = client.web_search(topic, model=tool_model)
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
            analysis = client.chat_completion(messages, model=chat_model)
            print(analysis)
            time.sleep(delay)

        if iterations <= 0:
            time.sleep(delay)


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
