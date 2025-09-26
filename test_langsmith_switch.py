#!/usr/bin/env python3
"""
测试LangSmith开关功能
"""

import os
import sys

def test_langsmith_switch():
    """测试LangSmith开关功能"""
    print("🧪 测试LangSmith开关功能")
    print("=" * 50)
    
    # 保存原始环境变量
    original_key = os.getenv("LANGSMITH_API_KEY")
    
    # 测试场景1：有API key但禁用LangSmith
    if original_key:
        print("\n📋 测试场景1：有API key但禁用LangSmith")
        print("命令: python bigmodel_loop.py --disable-langsmith --topics '测试' --iterations 1")
        
    # 测试场景2：有API key且启用LangSmith
    if original_key:
        print("\n📋 测试场景2：有API key且启用LangSmith")
        print("命令: python bigmodel_loop.py --enable-langsmith --topics '测试' --iterations 1")
        
    # 测试场景3：没有API key
    print("\n📋 测试场景3：没有API key")
    print("命令: LANGSMITH_API_KEY= python bigmodel_loop.py --topics '测试' --iterations 1")
    
    # 显示当前状态
    print(f"\n📊 当前环境状态:")
    print(f"   LANGSMITH_API_KEY: {'✅ 已设置' if original_key else '❌ 未设置'}")
    print(f"   LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT', '❌ 未设置')}")
    
    # 并发模式测试
    print(f"\n📋 并发模式测试:")
    print("# 禁用LangSmith的并发执行")
    print("python concurrent_bigmodel.py --disable-langsmith --topics '测试' --concurrency 2 --iterations 1")
    
    print("\n# 启用LangSmith的并发执行")
    print("python concurrent_bigmodel.py --enable-langsmith --topics '测试' --concurrency 2 --iterations 1")


if __name__ == "__main__":
    test_langsmith_switch()