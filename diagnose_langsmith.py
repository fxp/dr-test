#!/usr/bin/env python3
"""
LangSmith 追踪诊断和修复工具
"""

import os
from dotenv import load_dotenv

def diagnose_langsmith():
    """诊断 LangSmith 配置和连接"""
    load_dotenv()
    
    print("🔍 LangSmith 追踪诊断")
    print("=" * 50)
    
    # 1. 检查环境变量
    print("1️⃣ 检查环境变量...")
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT") 
    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    print(f"   LANGSMITH_API_KEY: {'✅ 已设置' if langsmith_key else '❌ 未设置'}")
    print(f"   LANGSMITH_PROJECT: {langsmith_project or '❌ 未设置'}")
    print(f"   LANGSMITH_ENDPOINT: {langsmith_endpoint}")
    
    if not langsmith_key:
        print("❌ 缺少 LANGSMITH_API_KEY，无法进行追踪")
        return False
    
    # 2. 测试 LangSmith 连接
    print("\n2️⃣ 测试 LangSmith 连接...")
    try:
        from langsmith import Client
        client = Client(
            api_key=langsmith_key,
            api_url=langsmith_endpoint
        )
        
        # 测试连接
        info = client.info
        print(f"   ✅ 连接成功")
        print(f"   客户端信息: {type(info)}")
        
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False
    
    # 3. 检查项目
    print(f"\n3️⃣ 检查项目 '{langsmith_project}'...")
    try:
        # 尝试读取项目信息
        projects = list(client.list_projects())
        project_names = [p.name for p in projects]
        
        if langsmith_project in project_names:
            print(f"   ✅ 项目 '{langsmith_project}' 存在")
        else:
            print(f"   ⚠️  项目 '{langsmith_project}' 不存在，将自动创建")
            print(f"   可用项目: {project_names}")
            
    except Exception as e:
        print(f"   ⚠️  无法检查项目: {e}")
    
    # 4. 测试手动创建追踪
    print(f"\n4️⃣ 测试手动创建追踪...")
    try:
        from langsmith import traceable
        
        @traceable(name="test_trace", project_name=langsmith_project)
        def test_function(input_data):
            return {"result": "test successful", "input": input_data}
        
        result = test_function("LangSmith 测试")
        print(f"   ✅ 手动追踪创建成功")
        print(f"   结果: {result}")
        
    except Exception as e:
        print(f"   ❌ 手动追踪失败: {e}")
        return False
    
    # 5. 测试 OpenAI 包装
    print(f"\n5️⃣ 测试 OpenAI 包装...")
    try:
        from langsmith.wrappers import wrap_openai
        from openai import OpenAI
        
        # 创建测试客户端
        test_client = OpenAI(
            api_key="test_key",
            base_url="https://api.openai.com/v1/"  # 使用标准端点测试
        )
        
        wrapped_client = wrap_openai(test_client)
        print(f"   ✅ OpenAI 包装成功")
        
    except Exception as e:
        print(f"   ❌ OpenAI 包装失败: {e}")
        return False
    
    print(f"\n✅ 所有检查通过！")
    print(f"\n📊 查看追踪: https://smith.langchain.com/projects/{langsmith_project}")
    return True


def fix_langsmith_issues():
    """修复常见的 LangSmith 问题"""
    print("\n🔧 修复 LangSmith 配置...")
    
    # 1. 设置必需的环境变量
    print("1️⃣ 设置 LangSmith 环境变量...")
    
    # 设置 LangChain 的环境变量（LangSmith 需要）
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT")
    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    if langsmith_key:
        os.environ["LANGCHAIN_API_KEY"] = langsmith_key
        print(f"   设置 LANGCHAIN_API_KEY")
    
    if langsmith_project:
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        print(f"   设置 LANGCHAIN_PROJECT={langsmith_project}")
    
    # 启用追踪
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    print("   设置 LANGCHAIN_TRACING_V2=true")
    
    os.environ["LANGCHAIN_ENDPOINT"] = langsmith_endpoint
    print(f"   设置 LANGCHAIN_ENDPOINT={langsmith_endpoint}")
    
    print("✅ 配置修复完成")


def test_full_integration():
    """测试完整集成"""
    print("\n🧪 测试完整集成...")
    
    try:
        from bigmodel_loop import BigModelClient
        
        api_key = os.getenv("BIGMODEL_API_KEY")
        if not api_key:
            print("❌ 缺少 BIGMODEL_API_KEY")
            return False
        
        # 创建客户端
        client = BigModelClient(api_key=api_key)
        print("✅ BigModelClient 创建成功")
        
        # 测试搜索（应该创建追踪）
        print("🔍 测试搜索追踪...")
        results = client.web_search("测试查询", top_k=2)
        print(f"✅ 搜索完成，结果数: {len(results)}")
        
        # 测试聊天（应该创建追踪）
        print("💬 测试聊天追踪...")
        messages = [
            {"role": "system", "content": "你是一个测试助手"},
            {"role": "user", "content": "请简单回复一句话进行测试"}
        ]
        response = client.chat_completion(messages)
        print(f"✅ 聊天完成，响应长度: {len(response)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔍 LangSmith 追踪诊断工具")
    print("=" * 60)
    
    # 诊断
    success = diagnose_langsmith()
    
    if success:
        # 修复配置
        fix_langsmith_issues()
        
        # 完整测试
        integration_success = test_full_integration()
        
        print("\n" + "=" * 60)
        if integration_success:
            print("🎉 LangSmith 追踪配置正确！")
            print("💡 如果仍未看到追踪，请检查:")
            print("   1. LangSmith 控制台项目是否正确")
            print("   2. 网络连接是否正常")
            print("   3. 等待几秒钟让追踪数据同步")
        else:
            print("❌ 集成测试失败，请检查错误信息")
    else:
        print("\n❌ LangSmith 配置有问题，请先修复基本配置")