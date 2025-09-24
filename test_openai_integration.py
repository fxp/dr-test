#!/usr/bin/env python3
"""
测试 OpenAI SDK 集成和 LangSmith 追踪功能
"""

import os
from dotenv import load_dotenv
from bigmodel_loop import BigModelClient

def test_openai_integration():
    """测试 OpenAI SDK 集成"""
    load_dotenv()
    
    print("🔄 测试 OpenAI SDK 集成和 LangSmith 追踪...")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv("BIGMODEL_API_KEY")
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT")
    
    print(f"🔑 BIGMODEL_API_KEY: {'✅ 已设置' if api_key else '❌ 未设置'}")
    print(f"📊 LANGSMITH_API_KEY: {'✅ 已设置' if langsmith_key else '❌ 未设置'}")
    print(f"📁 LANGSMITH_PROJECT: {langsmith_project or '❌ 未设置'}")
    
    if not api_key:
        print("❌ 缺少 BigModel API Key")
        return False
    
    try:
        # 初始化客户端
        client = BigModelClient(api_key=api_key)
        print("✅ BigModelClient 初始化成功（使用 OpenAI SDK）")
        
        # 测试 Web Search（带 LangSmith 追踪）
        print("\\n🔍 测试 Web Search...")
        search_results = client.web_search("人工智能", top_k=3)
        print(f"✅ Web Search 成功，返回 {len(search_results)} 条结果")
        
        if search_results:
            print(f"   示例结果: {search_results[0]['title'][:50]}...")
        
        # 测试 Chat Completion（使用 OpenAI SDK + LangSmith）
        print("\\n💬 测试 Chat Completion...")
        messages = [
            {"role": "system", "content": "你是一个有用的助手。"},
            {"role": "user", "content": "简单介绍一下人工智能的发展趋势"}
        ]
        
        response = client.chat_completion(messages)
        print(f"✅ Chat Completion 成功，响应长度: {len(response)} 字符")
        print(f"   响应预览: {response[:100]}...")
        
        print("\\n🎉 所有测试通过！")
        
        if langsmith_key:
            print(f"\\n📊 LangSmith 追踪已启用")
            print(f"   项目: {langsmith_project}")
            print(f"   查看追踪: https://smith.langchain.com/projects/{langsmith_project}")
        else:
            print("\\n⚠️  LangSmith 追踪未启用（没有 API Key）")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_environment_loading():
    """测试环境变量加载"""
    load_dotenv()
    
    print("\\n🔧 环境变量配置:")
    env_vars = [
        "BIGMODEL_API_KEY",
        "LANGSMITH_API_KEY", 
        "LANGSMITH_PROJECT",
        "DEFAULT_CHAT_MODEL",
        "DEFAULT_TOOL_MODEL",
        "SEARCH_ENGINE"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 隐藏 API Key 的部分内容
            if "KEY" in var:
                display_value = f"{value[:20]}..." if len(value) > 20 else value
            else:
                display_value = value
            print(f"   {var}: {display_value}")
        else:
            print(f"   {var}: ❌ 未设置")


if __name__ == "__main__":
    print("🧪 BigModel OpenAI SDK 和 LangSmith 集成测试")
    print("=" * 60)
    
    test_environment_loading()
    
    print("\\n" + "=" * 60)
    success = test_openai_integration()
    
    print("\\n" + "=" * 60)
    if success:
        print("🎉 集成测试完成！现在可以使用以下命令运行完整分析:")
        print("   python bigmodel_loop.py --topics '自动驾驶' '智能制造' --iterations 1")
    else:
        print("❌ 测试失败，请检查配置")