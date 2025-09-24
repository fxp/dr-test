# 环境变量配置指南

## 📁 文件说明

- **`.env`**: 实际的环境变量配置文件（包含真实的API密钥）
- **`.env.example`**: 环境变量模板文件（用于参考和初始化）
- **`load_env.sh`**: Bash环境变量加载脚本
- **`env_loader.py`**: Python环境变量加载器

## 🚀 快速开始

### 1. 创建配置文件
```bash
# 复制模板文件
cp .env.example .env

# 编辑配置
nano .env
```

### 2. 配置API密钥
在 `.env` 文件中设置：
```bash
BIGMODEL_API_KEY=your_actual_api_key_here
```

### 3. 使用方式

#### 方式一：使用 Bash 脚本加载
```bash
# 加载环境变量
source load_env.sh

# 运行脚本
python bigmodel_loop.py --topics "自动驾驶" "智能制造" --iterations 1
```

#### 方式二：直接运行（自动加载 .env）
```bash
# Python 脚本会自动加载 .env 文件
python bigmodel_loop.py --topics "自动驾驶" "智能制造" --iterations 1
```

#### 方式三：手动设置环境变量
```bash
export BIGMODEL_API_KEY="your_api_key"
export LANGSMITH_API_KEY="your_langsmith_key"
export LANGSMITH_PROJECT="bigmodel-analysis"
python bigmodel_loop.py --topics "自动驾驶" "智能制造" --iterations 1
```

## ⚙️ 配置项说明

### 必需配置
- `BIGMODEL_API_KEY`: BigModel API 密钥（从 [bigmodel.cn](https://bigmodel.cn) 获取）

### 可选配置
- `LANGSMITH_API_KEY`: LangSmith API 密钥（用于跟踪监控）
- `LANGSMITH_PROJECT`: LangSmith 项目名称
- `DEFAULT_TOPICS`: 默认分析话题（逗号分隔）
- `DEFAULT_ITERATIONS`: 默认运行轮次
- `DEFAULT_DELAY`: 请求间延迟时间（秒）
- `DEFAULT_CHAT_MODEL`: 默认聊天模型
- `DEFAULT_TOOL_MODEL`: 默认工具模型
- `SEARCH_ENGINE`: 搜索引擎类型
- `SEARCH_CONTENT_SIZE`: 搜索内容大小
- `SEARCH_COUNT`: 搜索结果数量

## 🔒 安全提醒

1. **永远不要提交 `.env` 文件到版本控制**
2. 将 `.env` 添加到 `.gitignore`
3. 使用 `.env.example` 作为模板分享
4. 定期轮换 API 密钥

## 🛠️ 工具命令

### 查看当前配置
```bash
python env_loader.py
```

### 验证环境变量
```bash
source load_env.sh
```

### 测试配置
```bash
python test_langsmith.py
```

## 🔧 故障排除

### 问题：API 密钥错误
```bash
# 检查环境变量是否正确加载
echo $BIGMODEL_API_KEY

# 重新加载配置
source load_env.sh
```

### 问题：LangSmith 不工作
```bash
# 检查 LangSmith 配置
echo $LANGSMITH_API_KEY
echo $LANGSMITH_PROJECT

# 安装 LangSmith（如果需要）
pip install langsmith
```

### 问题：.env 文件不存在
```bash
# 从模板创建
cp .env.example .env

# 编辑配置
nano .env
```