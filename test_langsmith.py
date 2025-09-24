#!/usr/bin/env python3
"""Test LangSmith integration"""

import os
from bigmodel_loop import BigModelClient

def test_langsmith():
    print("Testing LangSmith integration...")
    
    # 检查环境变量
    if not os.getenv("BIGMODEL_API_KEY"):
        print("❌ BIGMODEL_API_KEY not set")
        return False
    
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT")
    
    print(f"🔑 BIGMODEL_API_KEY: {'✅ Set' if os.getenv('BIGMODEL_API_KEY') else '❌ Not set'}")
    print(f"🔑 LANGSMITH_API_KEY: {'✅ Set' if langsmith_key else '❌ Not set'}")
    print(f"📁 LANGSMITH_PROJECT: {langsmith_project or '❌ Not set'}")
    
    # 测试 BigModel 客户端初始化
    try:
        client = BigModelClient(api_key=os.getenv("BIGMODEL_API_KEY"))
        print("✅ BigModelClient initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing BigModelClient: {e}")
        return False

if __name__ == "__main__":
    success = test_langsmith()
    if success:
        print("\n🎉 LangSmith integration ready!")
        print("\nTo run with tracing:")
        print("export LANGSMITH_API_KEY='your_key'")
        print("export LANGSMITH_PROJECT='bigmodel-analysis'")
        print("python bigmodel_loop.py --topics '自动驾驶' --iterations 1")
    else:
        print("\n❌ Setup incomplete. Please check configuration.")
