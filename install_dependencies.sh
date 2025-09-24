#!/bin/bash
# BigModel Loop Analysis - 依赖安装脚本

echo "🚀 BigModel Loop Analysis - 依赖安装"
echo "=================================="

# 检查Python版本
echo "🐍 检查Python版本..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "   当前Python版本: $python_version"

# 推荐创建虚拟环境
echo ""
echo "💡 推荐使用虚拟环境:"
echo "   python3 -m venv .venv"
echo "   source .venv/bin/activate  # Linux/Mac"
echo "   # .venv\\Scripts\\activate  # Windows"

# 安装依赖
echo ""
echo "📦 安装生产依赖..."
pip install -r requirements.txt

echo ""
echo "🔧 可选：安装开发依赖..."
read -p "是否安装开发工具 (pytest, black, mypy 等)? [y/N]: " install_dev

if [[ $install_dev =~ ^[Yy]$ ]]; then
    echo "📦 安装开发依赖..."
    pip install -r requirements-dev.txt
    echo "✅ 开发依赖安装完成"
else
    echo "⏭️ 跳过开发依赖安装"
fi

# 验证安装
echo ""
echo "✅ 验证安装..."
python3 -c "
import requests
import openai
from dotenv import load_dotenv
print('✅ 核心依赖检查通过')

try:
    import langsmith
    print('✅ LangSmith 可用')
except ImportError:
    print('⚠️  LangSmith 不可用（可选依赖）')
"

echo ""
echo "🎉 依赖安装完成！"
echo ""
echo "📋 下一步:"
echo "1. 复制配置文件: cp .env.example .env"
echo "2. 编辑配置: nano .env"
echo "3. 运行测试: python3 test_openai_integration.py"
echo "4. 开始分析: python3 bigmodel_loop.py --topics '人工智能' --iterations 1"