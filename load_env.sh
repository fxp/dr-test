#!/bin/bash
# 环境变量加载脚本
# 使用方法: source load_env.sh

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在！"
    echo "📝 请从 .env.example 复制并配置："
    echo "   cp .env.example .env"
    echo "   nano .env"
    return 1 2>/dev/null || exit 1
fi

# 加载环境变量
echo "🔄 正在加载环境变量..."
set -a  # 自动导出所有变量
source .env
set +a

# 验证必需的变量
if [ -z "$BIGMODEL_API_KEY" ] || [ "$BIGMODEL_API_KEY" = "your_bigmodel_api_key_here" ]; then
    echo "❌ BIGMODEL_API_KEY 未配置或使用默认值"
    echo "📝 请在 .env 文件中设置有效的 API Key"
    return 1 2>/dev/null || exit 1
fi

# 显示配置状态
echo "✅ 环境变量加载成功！"
echo
echo "📋 当前配置："
echo "🔑 BIGMODEL_API_KEY: ${BIGMODEL_API_KEY:0:20}..."
echo "🏷️  DEFAULT_CHAT_MODEL: $DEFAULT_CHAT_MODEL"
echo "🏷️  DEFAULT_TOOL_MODEL: $DEFAULT_TOOL_MODEL"
echo "🔍 SEARCH_ENGINE: $SEARCH_ENGINE"
echo "📊 DEFAULT_TOPICS: $DEFAULT_TOPICS"
echo "🔄 DEFAULT_ITERATIONS: $DEFAULT_ITERATIONS"
echo "⏱️  DEFAULT_DELAY: $DEFAULT_DELAY"

# 检查 LangSmith 配置
if [ -n "$LANGSMITH_API_KEY" ] && [ "$LANGSMITH_API_KEY" != "your_langsmith_api_key_here" ]; then
    echo "📊 LANGSMITH_API_KEY: ${LANGSMITH_API_KEY:0:20}..."
    echo "📁 LANGSMITH_PROJECT: $LANGSMITH_PROJECT"
    echo "🎯 LangSmith 跟踪: ✅ 已启用"
else
    echo "🎯 LangSmith 跟踪: ❌ 未配置"
fi

echo
echo "🚀 现在可以运行脚本："
echo "   python bigmodel_loop.py --topics \"自动驾驶\" \"智能制造\" --iterations 1"