#!/usr/bin/env python3
"""
环境变量加载器
支持从 .env 文件加载配置
"""

import os
from typing import Dict, Optional


def load_env_file(env_file: str = ".env") -> Dict[str, str]:
    """从 .env 文件加载环境变量"""
    env_vars = {}
    
    if not os.path.exists(env_file):
        return env_vars
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if line.startswith('#') or not line:
                continue
            
            # 解析 KEY=VALUE 格式
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 移除引号
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                env_vars[key] = value
    
    return env_vars


def load_and_set_env(env_file: str = ".env", override: bool = False) -> None:
    """加载 .env 文件并设置环境变量"""
    env_vars = load_env_file(env_file)
    
    for key, value in env_vars.items():
        if override or key not in os.environ:
            os.environ[key] = value


def get_env_config() -> Dict[str, Optional[str]]:
    """获取所有配置，优先级：环境变量 > .env 文件 > 默认值"""
    
    # 先加载 .env 文件（不覆盖现有环境变量）
    load_and_set_env()
    
    config = {
        # API 配置
        'BIGMODEL_API_KEY': os.getenv('BIGMODEL_API_KEY'),
        'LANGSMITH_API_KEY': os.getenv('LANGSMITH_API_KEY'),
        'LANGSMITH_PROJECT': os.getenv('LANGSMITH_PROJECT', 'bigmodel-analysis'),
        'LANGSMITH_ENDPOINT': os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com'),
        
        # 脚本配置
        'DEFAULT_TOPICS': os.getenv('DEFAULT_TOPICS', '人工智能热点,新能源产业,医疗科技创新'),
        'DEFAULT_ITERATIONS': os.getenv('DEFAULT_ITERATIONS', '1'),
        'DEFAULT_DELAY': os.getenv('DEFAULT_DELAY', '3.0'),
        'DEFAULT_CHAT_MODEL': os.getenv('DEFAULT_CHAT_MODEL', 'glm-4.5-aq'),
        'DEFAULT_TOOL_MODEL': os.getenv('DEFAULT_TOOL_MODEL', 'glm-4.5-aq'),
        
        # 搜索配置
        'SEARCH_ENGINE': os.getenv('SEARCH_ENGINE', 'search-prime-aqdr'),
        'SEARCH_CONTENT_SIZE': os.getenv('SEARCH_CONTENT_SIZE', 'medium'),
        'SEARCH_COUNT': os.getenv('SEARCH_COUNT', '5'),
    }
    
    return config


def print_config_status():
    """打印配置状态"""
    config = get_env_config()
    
    print("📋 当前配置:")
    print("=" * 50)
    
    # API 配置
    api_key = config.get('BIGMODEL_API_KEY')
    if api_key and api_key != 'your_bigmodel_api_key_here':
        print(f"🔑 BIGMODEL_API_KEY: {api_key[:20]}...")
    else:
        print("🔑 BIGMODEL_API_KEY: ❌ 未配置")
    
    langsmith_key = config.get('LANGSMITH_API_KEY')
    if langsmith_key and langsmith_key != 'your_langsmith_api_key_here':
        print(f"📊 LANGSMITH_API_KEY: {langsmith_key[:20]}...")
        print(f"📁 LANGSMITH_PROJECT: {config.get('LANGSMITH_PROJECT')}")
        print("🎯 LangSmith 跟踪: ✅ 已启用")
    else:
        print("🎯 LangSmith 跟踪: ❌ 未配置")
    
    print()
    
    # 模型配置
    print("🤖 模型配置:")
    print(f"💬 Chat Model: {config.get('DEFAULT_CHAT_MODEL')}")
    print(f"🔧 Tool Model: {config.get('DEFAULT_TOOL_MODEL')}")
    print(f"🔍 Search Engine: {config.get('SEARCH_ENGINE')}")
    
    print()
    
    # 运行配置
    print("⚙️  运行配置:")
    print(f"📝 默认话题: {config.get('DEFAULT_TOPICS')}")
    print(f"🔄 默认迭代: {config.get('DEFAULT_ITERATIONS')}")
    print(f"⏱️  默认延迟: {config.get('DEFAULT_DELAY')}秒")
    print(f"📊 搜索结果数: {config.get('SEARCH_COUNT')}")


if __name__ == "__main__":
    print("🔄 加载环境变量配置...")
    print_config_status()