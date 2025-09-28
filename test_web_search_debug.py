#!/usr/bin/env python3
"""测试 Web Search 调用的调试脚本"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 确保环境变量设置
os.environ["SEARCH_ENGINE"] = "search-prime-aqdr"
os.environ["SEARCH_CONTENT_SIZE"] = "medium"

# 导入并测试
from bigmodel_loop import BigModelClient, setup_langsmith

def test_web_search_direct():
    """直接测试 BigModelClient 的 web_search 方法"""
    print("=" * 60)
    print("🧪 测试直接调用 BigModelClient.web_search")
    print("=" * 60)
    
    # 禁用 LangSmith 避免配额问题
    setup_langsmith(enable_langsmith=False)
    
    # 获取 API key
    api_key = os.getenv("BIGMODEL_API_KEY")
    if not api_key:
        print("❌ 缺少 BIGMODEL_API_KEY 环境变量")
        return False
    
    try:
        # 创建客户端
        print(f"🔧 创建 BigModelClient...")
        client = BigModelClient(api_key=api_key)
        
        # 测试 web search
        test_query = "人工智能最新发展"
        print(f"🔍 测试查询: {test_query}")
        print(f"📋 环境变量:")
        print(f"   - SEARCH_ENGINE: {os.getenv('SEARCH_ENGINE')}")
        print(f"   - SEARCH_CONTENT_SIZE: {os.getenv('SEARCH_CONTENT_SIZE')}")
        print()
        
        results = client.web_search(test_query, model="glm-4.5-aq", top_k=3)
        
        print(f"✅ Web Search 成功完成!")
        print(f"📊 结果统计:")
        print(f"   - 查询: {test_query}")
        print(f"   - 结果数量: {len(results)}")
        print(f"   - 前3个结果标题:")
        
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', '无标题')[:50]
            print(f"     {i}. {title}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Web Search 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_web_search():
    """测试并发模式下的 web search 调用"""
    print("\\n" + "=" * 60)
    print("🧪 测试并发模式下的 Web Search 调用")
    print("=" * 60)
    
    try:
        from concurrent_bigmodel import TaskWorker
        
        # 获取 API key
        api_key = os.getenv("BIGMODEL_API_KEY")
        if not api_key:
            print("❌ 缺少 BIGMODEL_API_KEY 环境变量")
            return False
        
        # 创建 TaskWorker
        print(f"🔧 创建 TaskWorker...")
        worker = TaskWorker(
            api_key=api_key,
            chat_model="glm-4.5-aq",
            tool_model="glm-4.5-aq", 
            worker_id="TEST-1"
        )
        
        # 测试单个话题处理
        test_topic = "区块链技术应用"
        print(f"🔍 测试话题: {test_topic}")
        print()
        
        result = worker.process_topic(test_topic)
        
        print(f"✅ 并发 Web Search 测试成功!")
        print(f"📊 处理结果:")
        print(f"   - 话题: {result.topic}")
        print(f"   - 成功: {result.success}")
        print(f"   - 搜索结果数: {result.search_results_count}")
        print(f"   - 执行时间: {result.execution_time:.2f}s")
        print(f"   - Worker ID: {result.worker_id}")
        
        if result.analysis:
            analysis_preview = result.analysis[:200].replace('\\n', ' ')
            print(f"   - 分析预览: {analysis_preview}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 并发 Web Search 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始 Web Search 调试测试")
    print(f"🔧 Python 路径: {sys.executable}")
    print(f"📂 工作目录: {os.getcwd()}")
    print()
    
    # 测试1: 直接调用
    success1 = test_web_search_direct()
    
    # 测试2: 并发调用 
    success2 = test_concurrent_web_search()
    
    print("\\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    print(f"✅ 直接调用测试: {'通过' if success1 else '失败'}")
    print(f"✅ 并发调用测试: {'通过' if success2 else '失败'}")
    
    if success1 and success2:
        print("🎉 所有 Web Search 调用测试通过!")
        exit(0)
    else:
        print("❌ 部分测试失败，请检查日志")
        exit(1)