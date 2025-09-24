# BigModel + OpenAI SDK + LangSmith 集成指南

## 🚀 新功能特性

### ✅ 已完成的升级

1. **OpenAI SDK 集成**
   - 使用官方 OpenAI Python SDK 调用 BigModel API
   - 完全兼容 OpenAI API 格式
   - 自动错误处理和重试机制

2. **增强的 LangSmith 追踪**
   - **Chat Completion**: 自动追踪 OpenAI SDK 调用（模型、参数、token使用量等）
   - **Web Search**: 手动追踪搜索请求（查询、结果数量、搜索引擎等）
   - **完整流程**: 追踪整个分析周期（迭代、话题、耗时等）

3. **环境变量管理**
   - 使用 `.env` 文件管理所有配置
   - 自动加载环境变量
   - 支持配置验证和状态显示

## 📋 LangSmith 追踪层级

```
topic_analysis_cycle (整个循环)
├── analysis_iteration (每轮迭代)
│   ├── single_topic_analysis (单个话题分析)
│   │   ├── web_search (网页搜索)
│   │   │   ├── 搜索参数: query, search_engine, count
│   │   │   ├── 搜索结果: results_count, results
│   │   │   └── 耗时统计
│   │   └── chat_completion (OpenAI SDK)
│   │       ├── 模型参数: model, temperature
│   │       ├── 消息内容: system + user prompt
│   │       ├── Token 使用量 (自动追踪)
│   │       └── 响应内容和耗时
│   └── 迭代汇总: topics_count, models
└── 循环统计: iterations, total_topics
```

## 🛠️ 使用方法

### 1. 环境配置
```bash
# 加载环境变量
source load_env.sh

# 或者手动设置
export BIGMODEL_API_KEY="your_api_key"
export LANGSMITH_API_KEY="your_langsmith_key"
export LANGSMITH_PROJECT="bigmodel-analysis"
```

### 2. 运行测试
```bash
# 测试所有功能
python test_openai_integration.py

# 测试基本配置
python env_loader.py
```

### 3. 运行分析
```bash
# 单次分析
python bigmodel_loop.py --topics "自动驾驶" "智能制造" --iterations 1

# 持续分析
python bigmodel_loop.py --topics "AI热点" "新能源" --iterations 0 --delay 10

# 自定义模型
python bigmodel_loop.py --topics "区块链" --chat-model "glm-4.5-aq" --iterations 1
```

## 📊 LangSmith 数据查看

### 1. 访问控制台
- 登录: https://smith.langchain.com
- 选择项目: `bigmodel` (或您设置的项目名)

### 2. 查看追踪数据
- **执行追踪**: 查看每次API调用的详细信息
- **性能监控**: API响应时间、成功率统计
- **成本分析**: Token使用量和成本估算
- **错误监控**: 失败请求和错误详情

### 3. 追踪信息包含
- **搜索调用**: 
  - 输入: 查询词、搜索引擎、参数设置
  - 输出: 搜索结果数量、标题、摘要
  - 元数据: 耗时、搜索引擎类型
  
- **聊天调用**:
  - 输入: 模型名称、消息内容、参数
  - 输出: 生成文本、token统计
  - 元数据: 响应时间、模型版本

## 🔧 配置选项

### 环境变量
```bash
# 必需配置
BIGMODEL_API_KEY=your_api_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=your_project_name

# 可选配置
DEFAULT_CHAT_MODEL=glm-4.5-aq
DEFAULT_TOOL_MODEL=glm-4.5-aq
SEARCH_ENGINE=search-prime-aqdr
SEARCH_CONTENT_SIZE=medium
DEFAULT_TOPICS=人工智能热点,新能源产业,医疗科技创新
DEFAULT_ITERATIONS=1
DEFAULT_DELAY=3.0
```

### 命令行参数
```bash
--topics "话题1" "话题2"      # 分析话题
--iterations N              # 运行轮次 (0=无限循环)
--delay N                   # 请求间延迟(秒)
--chat-model MODEL          # 聊天模型
--tool-model MODEL          # 工具模型
```

## 🚨 故障排除

### 1. OpenAI SDK 错误
```bash
# 检查配置
echo $BIGMODEL_API_KEY
echo $OPENAI_BASE_URL

# 重新测试
python test_openai_integration.py
```

### 2. LangSmith 连接问题
```bash
# 验证 API Key
echo $LANGSMITH_API_KEY

# 测试连接
python -c "from langsmith import Client; print(Client().info())"
```

### 3. 环境变量问题
```bash
# 重新加载
source load_env.sh

# 查看配置
python env_loader.py
```

## 🎯 最佳实践

1. **开发阶段**: 使用少量迭代测试 (`--iterations 1`)
2. **生产运行**: 设置适当延迟避免API限制 (`--delay 5`)
3. **LangSmith**: 定期查看追踪数据优化提示词
4. **监控**: 关注token使用量和响应时间
5. **错误处理**: 查看LangSmith错误日志定位问题

## 📈 性能优化建议

- **并发控制**: 避免过快的连续请求
- **提示词优化**: 基于LangSmith数据优化提示词效果
- **模型选择**: 根据任务复杂度选择合适模型
- **结果缓存**: 考虑对重复查询进行缓存
- **批量处理**: 对于大量话题，考虑批量分析