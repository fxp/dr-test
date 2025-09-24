# LangSmith 集成设置指南

## 1. 获取 LangSmith API Key

1. 访问 [LangSmith 官网](https://smith.langchain.com/)
2. 注册或登录账户
3. 在设置页面创建 API Key
4. 创建一个项目（例如：`bigmodel-analysis`）

## 2. 环境变量配置

```bash
# 设置 LangSmith API Key
export LANGSMITH_API_KEY="your_langsmith_api_key_here"

# 设置项目名称
export LANGSMITH_PROJECT="bigmodel-analysis"

# 可选：设置跟踪端点（默认不需要设置）
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
```

## 3. 运行带 LangSmith 跟踪的脚本

```bash
# 完整命令示例
export BIGMODEL_API_KEY="your_bigmodel_api_key"
export LANGSMITH_API_KEY="your_langsmith_api_key"
export LANGSMITH_PROJECT="bigmodel-analysis"

python bigmodel_loop.py --topics "自动驾驶" "智能制造" --iterations 1 --delay 2.0
```

## 4. LangSmith 跟踪功能

脚本会自动跟踪以下内容：

- **Web Search 调用**: 搜索查询、参数、响应时间、结果数量
- **Chat Completion 调用**: 提示内容、模型响应、响应时间、token 使用量
- **完整的对话链**: 从搜索到分析的完整流程

## 5. 在 LangSmith 中查看

1. 登录 LangSmith 控制台
2. 选择您的项目（如：`bigmodel-analysis`）
3. 查看实时跟踪数据：
   - 请求详情
   - 响应时间
   - 错误信息
   - 性能指标

## 6. 故障排除

如果 LangSmith 不可用：
- 脚本会自动回退到无跟踪模式
- 显示提示信息但不影响正常运行
- 可以稍后安装 `pip install langsmith` 来启用跟踪