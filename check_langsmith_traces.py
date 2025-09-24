#!/usr/bin/env python3
"""
LangSmith 追踪查看工具
"""

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

def check_langsmith_traces():
    """检查 LangSmith 中的追踪数据"""
    load_dotenv()
    
    print("📊 LangSmith 追踪数据检查")
    print("=" * 50)
    
    try:
        from langsmith import Client
        
        langsmith_key = os.getenv("LANGSMITH_API_KEY")
        langsmith_project = os.getenv("LANGSMITH_PROJECT", "bigmodel")
        langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        if not langsmith_key:
            print("❌ 缺少 LANGSMITH_API_KEY")
            return
        
        client = Client(
            api_key=langsmith_key,
            api_url=langsmith_endpoint
        )
        
        print(f"🔍 检查项目: {langsmith_project}")
        print(f"🌐 LangSmith URL: https://smith.langchain.com/projects/{langsmith_project}")
        
        # 获取最近的追踪数据
        print(f"\n📈 查询最近的追踪数据...")
        
        # 查询最近1小时的数据
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        runs = list(client.list_runs(
            project_name=langsmith_project,
            start_time=start_time,
            limit=10
        ))
        
        if runs:
            print(f"✅ 找到 {len(runs)} 条追踪记录")
            print(f"\n📋 最近的追踪记录:")
            
            for i, run in enumerate(runs[:5], 1):
                print(f"\n   {i}. 名称: {run.name}")
                print(f"      ID: {run.id}")
                print(f"      状态: {run.status}")
                print(f"      开始时间: {run.start_time}")
                if run.end_time:
                    duration = (run.end_time - run.start_time).total_seconds()
                    print(f"      持续时间: {duration:.2f}秒")
                
                # 显示输入输出信息
                if run.inputs:
                    input_keys = list(run.inputs.keys())[:2]  # 只显示前2个键
                    print(f"      输入: {input_keys}")
                
                if run.outputs:
                    output_keys = list(run.outputs.keys())[:2]  # 只显示前2个键  
                    print(f"      输出: {output_keys}")
        else:
            print("⚠️  没有找到追踪记录")
            print("\n可能的原因:")
            print("1. 追踪数据还在同步中（等待1-2分钟）")
            print("2. 项目名称不正确")
            print("3. 时间范围内没有运行追踪")
            
        # 检查项目是否存在
        print(f"\n🏗️  检查项目状态...")
        try:
            projects = list(client.list_projects())
            project_names = [p.name for p in projects]
            
            if langsmith_project in project_names:
                print(f"✅ 项目 '{langsmith_project}' 存在")
                
                # 获取项目详情
                for project in projects:
                    if project.name == langsmith_project:
                        print(f"   创建时间: {project.created_at}")
                        break
            else:
                print(f"⚠️  项目 '{langsmith_project}' 不存在")
                print(f"   可用项目: {project_names[:5]}...")  # 只显示前5个
                
        except Exception as e:
            print(f"❌ 检查项目失败: {e}")
            
    except Exception as e:
        print(f"❌ 连接 LangSmith 失败: {e}")
        import traceback
        traceback.print_exc()


def show_langsmith_urls():
    """显示 LangSmith 相关 URL"""
    langsmith_project = os.getenv("LANGSMITH_PROJECT", "bigmodel")
    
    print(f"\n🌐 LangSmith 相关链接:")
    print(f"📊 项目主页: https://smith.langchain.com/projects/{langsmith_project}")
    print(f"🔍 追踪列表: https://smith.langchain.com/projects/{langsmith_project}/traces")
    print(f"⚙️  项目设置: https://smith.langchain.com/projects/{langsmith_project}/settings")
    print(f"📈 性能监控: https://smith.langchain.com/projects/{langsmith_project}/monitoring")


if __name__ == "__main__":
    check_langsmith_traces()
    show_langsmith_urls()
    
    print(f"\n💡 提示:")
    print(f"1. 如果没有看到追踪，请等待1-2分钟让数据同步")
    print(f"2. 确保运行了带有追踪的脚本: python bigmodel_loop.py --topics '测试' --iterations 1") 
    print(f"3. 检查浏览器中的 LangSmith 项目页面")