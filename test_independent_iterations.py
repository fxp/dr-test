#!/usr/bin/env python3
"""
测试独立的 iteration 追踪
"""

import os
from dotenv import load_dotenv

def test_independent_iterations():
    """测试独立的 iteration 追踪"""
    load_dotenv()
    
    print("🧪 测试独立的 Iteration 追踪")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv("BIGMODEL_API_KEY")
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    
    if not api_key:
        print("❌ 缺少 BIGMODEL_API_KEY")
        return False
    
    if not langsmith_key:
        print("⚠️  没有 LangSmith 配置，将运行无追踪模式")
    else:
        print(f"✅ LangSmith 配置正确，项目: {os.getenv('LANGSMITH_PROJECT')}")
    
    try:
        from bigmodel_loop import BigModelClient, cycle_topics
        
        # 创建客户端
        client = BigModelClient(api_key=api_key)
        print("✅ BigModelClient 初始化成功")
        
        # 运行2轮测试，每轮2个话题
        print("\\n🔄 开始测试：2轮分析，每轮2个话题")
        print("   话题: ['AI技术', '新能源']")
        print("   预期: 在LangSmith中看到2个独立的trace")
        print("   - iteration_1")  
        print("   - iteration_2")
        
        cycle_topics(
            client=client,
            topics=["AI技术", "新能源"],
            iterations=2,
            delay=1.0,  # 短延迟以加速测试
            chat_model="glm-4.5-aq", 
            tool_model="glm-4.5-aq"
        )
        
        print("\\n✅ 测试完成！")
        
        if langsmith_key:
            langsmith_project = os.getenv("LANGSMITH_PROJECT", "bigmodel")
            print(f"\\n📊 查看LangSmith追踪:")
            print(f"   🌐 项目页面: https://smith.langchain.com/projects/{langsmith_project}")
            print(f"   🔍 追踪列表: https://smith.langchain.com/projects/{langsmith_project}/traces")
            print(f"\\n💡 预期看到:")
            print(f"   - iteration_1 (包含2个topic_analysis)")
            print(f"   - iteration_2 (包含2个topic_analysis)")
            print(f"   - 每个iteration是独立的trace，不嵌套在大的trace中")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_independent_iterations()
    
    if success:
        print("\\n" + "=" * 50)
        print("🎉 独立 Iteration 追踪测试成功！")
        print("\\n📋 新的追踪结构:")
        print("├── iteration_1 (独立trace)")  
        print("│   ├── topic_analysis: AI技术")
        print("│   │   ├── web_search") 
        print("│   │   └── chat_completion")
        print("│   └── topic_analysis: 新能源")
        print("│       ├── web_search")
        print("│       └── chat_completion")
        print("└── iteration_2 (独立trace)")
        print("    ├── topic_analysis: AI技术") 
        print("    │   ├── web_search")
        print("    │   └── chat_completion")
        print("    └── topic_analysis: 新能源")
        print("        ├── web_search")
        print("        └── chat_completion")
    else:
        print("\\n❌ 测试失败，请检查配置")