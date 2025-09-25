# 并发BigModel执行器使用指南

## 概述

`concurrent_bigmodel.py` 是一个支持N个并发的BigModel分析执行器，基于原始的 `bigmodel_loop.py` 扩展而来。它支持三种并发模式，提供完整的错误处理和进度监控。

## 特性

- ✅ **多种并发模式**: multiprocessing（多进程）, threading（多线程）, asyncio（异步）
- ✅ **灵活的并发控制**: 支持指定任意数量的并发worker
- ✅ **完整的错误处理**: 超时控制、重试机制、异常捕获
- ✅ **进度监控**: 实时显示执行进度和统计信息
- ✅ **结果输出**: JSON格式的详细结果保存
- ✅ **LangSmith集成**: 完整支持分布式追踪
- ✅ **优雅停止**: 支持Ctrl+C中断和信号处理

## 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 或者安装开发依赖（包含测试工具）
pip install -r requirements-dev.txt
```

## 快速开始

### 1. 基础使用

```bash
# 使用4个进程并发处理默认话题
python concurrent_bigmodel.py

# 指定话题和并发数
python concurrent_bigmodel.py --topics "AI技术" "新能源" "医疗科技" --concurrency 8

# 无限持续执行（每隔5秒执行一轮，直到Ctrl+C停止）
python concurrent_bigmodel.py --topics "AI技术" "新能源" --iterations 0 --delay 5
```

### 2. 不同并发模式

```bash
# 多进程模式（推荐，真正的并行）
python concurrent_bigmodel.py --mode multiprocessing --concurrency 4

# 多线程模式（适合I/O密集型）
python concurrent_bigmodel.py --mode threading --concurrency 8

# 异步模式（高效的I/O处理）
python concurrent_bigmodel.py --mode asyncio --concurrency 6
```

### 3. 高级配置

```bash
# 完整参数示例
python concurrent_bigmodel.py \\
    --topics "人工智能" "机器学习" "深度学习" "神经网络" "计算机视觉" \\
    --concurrency 6 \\
    --mode threading \\
    --iterations 3 \\
    --timeout 180 \\
    --delay 1.0 \\
    --output results.json \\
    --chat-model glm-4.5-aq \\
    --tool-model glm-4.5-aq

# 无限持续执行（直到手动停止）
python concurrent_bigmodel.py \\
    --topics "AI技术" "新能源" \\
    --concurrency 4 \\
    --iterations 0 \\
    --delay 10 \\
    --mode multiprocessing
```

## 参数说明

### 基础参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--api-key` | BigModel API密钥 | 环境变量`BIGMODEL_API_KEY` | `--api-key your_key` |
| `--topics` | 要分析的话题列表 | 5个默认话题 | `--topics "AI" "区块链"` |
| `--iterations` | 执行轮数 (0=无限执行) | 1 | `--iterations 3` 或 `--iterations 0` |

### 并发参数

| 参数 | 说明 | 默认值 | 推荐值 |
|------|------|--------|--------|
| `--concurrency` | 并发worker数量 | 4 | 4-8 |
| `--mode` | 并发模式 | multiprocessing | multiprocessing/threading |
| `--timeout` | 单任务超时(秒) | 120 | 60-300 |
| `--delay` | 任务间延迟(秒) | 0.5 | 0.5-2.0 |
| `--max-retries` | 最大重试次数 | 2 | 1-3 |

### 模型参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--chat-model` | 聊天模型 | glm-4.5-aq |
| `--tool-model` | 工具模型 | glm-4.5-aq |

### 输出参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output` | 结果输出文件 | 自动生成 |
| `--quiet` | 静默模式 | False |

## 持续执行模式

### 🔄 无限执行 (iterations=0)

启用持续执行模式，程序会不断循环执行分析任务，直到手动停止：

```bash
# 基础无限执行
python concurrent_bigmodel.py --iterations 0 --topics "AI技术" "新能源"

# 带延迟的无限执行（每10秒一轮）
python concurrent_bigmodel.py --iterations 0 --delay 10 --topics "市场动态" "科技热点"

# 高并发的无限执行
python concurrent_bigmodel.py \\
    --iterations 0 \\
    --concurrency 8 \\
    --mode multiprocessing \\
    --delay 30 \\
    --topics "人工智能" "新能源" "医疗科技" "智能制造" "金融科技"
```

**特性:**
- ✅ 自动循环执行，无需重启
- ✅ 优雅停止支持（Ctrl+C）
- ✅ 每轮执行独立记录和统计
- ✅ 支持所有并发模式
- ✅ 完整的LangSmith追踪

**使用场景:**
- 📊 **定期监控**: 持续跟踪特定话题的发展
- 🔍 **实时分析**: 对时效性强的内容进行持续分析
- 📈 **长期观察**: 观察趋势变化和发展模式
- ⚡ **压力测试**: 测试系统在长时间运行下的稳定性

**停止方式:**
```bash
# 方式1: Ctrl+C 优雅停止
# 方式2: 发送SIGTERM信号
kill -TERM <进程ID>

# 方式3: 使用timeout命令限制运行时间
timeout 1h python concurrent_bigmodel.py --iterations 0 --topics "AI技术"
```

## 并发模式选择

### 🚀 Multiprocessing（多进程）

**推荐使用**，真正的并行执行

```bash
python concurrent_bigmodel.py --mode multiprocessing --concurrency 4
```

**优点**:
- 真正的并行执行，不受GIL限制
- 进程间隔离，一个进程崩溃不影响其他
- 适合CPU密集型和I/O密集型任务

**缺点**:
- 启动开销较大
- 内存占用相对较多

**适用场景**: 大批量任务，对性能要求高

### 🧵 Threading（多线程）

```bash
python concurrent_bigmodel.py --mode threading --concurrency 8
```

**优点**:
- 启动快，资源占用少
- 适合I/O密集型任务
- 线程间通信方便

**缺点**:
- 受GIL限制，不是真正并行
- 线程安全需要考虑

**适用场景**: 网络请求密集，中等规模任务

### ⚡ Asyncio（异步）

```bash  
python concurrent_bigmodel.py --mode asyncio --concurrency 6
```

**优点**:
- 高效的I/O处理
- 单线程，无需考虑线程安全
- 资源占用最少

**缺点**:
- 复杂度相对较高
- 不适合CPU密集型任务

**适用场景**: 大量异步I/O，对资源使用敏感

## 性能优化建议

### 1. 并发数设置

```bash
# 根据机器配置调整
CPU_COUNT=$(nproc)

# I/O密集型（推荐）
CONCURRENCY=$((CPU_COUNT * 2))

# CPU密集型
CONCURRENCY=$CPU_COUNT

# 示例：8核机器
python concurrent_bigmodel.py --concurrency 16  # I/O密集
python concurrent_bigmodel.py --concurrency 8   # CPU密集
```

### 2. 超时设置

```bash
# 根据网络和任务复杂度调整
python concurrent_bigmodel.py --timeout 60   # 快速网络
python concurrent_bigmodel.py --timeout 180  # 慢速网络或复杂任务
```

### 3. 批量处理

```bash
# 大量任务时分批处理
python concurrent_bigmodel.py \\
    --topics $(echo {1..100} | tr ' ' '\\n' | sed 's/^/topic_/') \\
    --batch-size 10 \\
    --concurrency 8
```

## 监控和调试

### 1. 日志输出

```bash
# 详细日志
python concurrent_bigmodel.py --topics "AI" "区块链"

# 静默模式
python concurrent_bigmodel.py --quiet --output results.json

# 查看日志文件
tail -f concurrent_bigmodel.log
```

### 2. 结果分析

```bash
# 分析结果文件
python -c "
import json
with open('results.json') as f:
    data = json.load(f)
    print('总任务:', data['summary']['total_tasks'])
    print('成功率:', f\"{data['summary']['successful_tasks']/data['summary']['total_tasks']*100:.1f}%\")
    print('平均耗时:', f\"{data['summary']['average_execution_time']:.2f}s\")
"
```

### 3. LangSmith追踪

```bash
# 设置LangSmith环境变量
export LANGSMITH_API_KEY="your_langsmith_key"
export LANGSMITH_PROJECT="concurrent-bigmodel"

# 执行带追踪的任务
python concurrent_bigmodel.py --topics "AI技术" "新能源"

# 查看追踪结果
echo "访问: https://smith.langchain.com/projects/concurrent-bigmodel"
```

## 常见问题

### Q1: 出现连接超时错误？

```bash
# 增加超时时间和重试次数
python concurrent_bigmodel.py \\
    --timeout 300 \\
    --max-retries 3 \\
    --delay 2.0
```

### Q2: 内存占用过高？

```bash
# 降低并发数或使用线程模式
python concurrent_bigmodel.py \\
    --mode threading \\
    --concurrency 4
```

### Q3: API限流问题？

```bash
# 增加请求间延迟
python concurrent_bigmodel.py \\
    --delay 1.0 \\
    --concurrency 2
```

### Q4: 部分任务失败？

```bash
# 查看详细日志
tail -n 50 concurrent_bigmodel.log

# 或查看结果文件中的错误信息
python -c "
import json
with open('results.json') as f:
    data = json.load(f)
    for result in data['results']:
        if not result['success']:
            print(f'失败任务: {result[\"topic\"]} - {result[\"error_message\"]}')
"
```

## 测试和验证

### 1. 运行测试套件

```bash
# 运行完整测试
python test_concurrent.py

# 单独测试某种模式  
python -c "
from test_concurrent import test_multiprocessing
test_multiprocessing()
"
```

### 2. 性能基准测试

```bash
# 比较不同并发数的性能
for i in 1 2 4 8; do
    echo "测试并发数: $i"
    time python concurrent_bigmodel.py \\
        --concurrency $i \\
        --topics "AI" "区块链" \\
        --quiet
done
```

### 3. 压力测试

```bash
# 大量话题压力测试
python concurrent_bigmodel.py \\
    --topics $(seq 1 50 | sed 's/^/话题_/') \\
    --concurrency 8 \\
    --mode threading \\
    --output stress_test_results.json
```

## 示例脚本

### 1. 批量分析脚本

```bash
#!/bin/bash
# batch_analysis.sh

TOPICS=(
    "人工智能最新进展"
    "新能源汽车发展"  
    "医疗科技创新"
    "智能制造趋势"
    "金融科技发展"
    "云计算技术"
    "区块链应用"
    "物联网发展"
    "5G技术进展"
    "量子计算研究"
)

python concurrent_bigmodel.py \\
    --topics "${TOPICS[@]}" \\
    --concurrency 6 \\
    --mode multiprocessing \\
    --iterations 2 \\
    --output "batch_analysis_$(date +%Y%m%d_%H%M%S).json"
```

### 2. 定时执行脚本

```bash
#!/bin/bash
# scheduled_analysis.sh

# 每小时执行一次分析
while true; do
    echo "开始定时分析: $(date)"
    
    python concurrent_bigmodel.py \\
        --topics "科技热点" "市场动态" "政策解读" \\
        --concurrency 4 \\
        --quiet \\
        --output "hourly_analysis_$(date +%Y%m%d_%H).json"
    
    echo "分析完成，等待下次执行..."
    sleep 3600  # 等待1小时
done
```

## 集成使用

### 1. Python脚本集成

```python
from concurrent_bigmodel import ConcurrentBigModelExecutor, ConcurrentConfig

# 创建配置
config = ConcurrentConfig(
    concurrency=6,
    mode="threading",
    timeout=120
)

# 创建执行器
executor = ConcurrentBigModelExecutor(
    config=config,
    api_key="your_api_key"
)

# 执行分析
topics = ["AI技术", "新能源", "医疗科技"]
results = executor.execute_concurrent(topics, iterations=1)

# 处理结果
for result in results:
    if result.success:
        print(f"话题: {result.topic}")
        print(f"分析: {result.analysis[:200]}...")
    else:
        print(f"失败: {result.topic} - {result.error_message}")
```

### 2. API封装示例

```python
from flask import Flask, request, jsonify
from concurrent_bigmodel import ConcurrentBigModelExecutor, ConcurrentConfig

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze_topics():
    data = request.json
    topics = data.get('topics', [])
    concurrency = data.get('concurrency', 4)
    
    config = ConcurrentConfig(concurrency=concurrency)
    executor = ConcurrentBigModelExecutor(config, api_key="your_key")
    
    results = executor.execute_concurrent(topics)
    
    return jsonify({
        'results': [asdict(result) for result in results]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## 最佳实践

1. **合理设置并发数**: 根据机器性能和网络条件调整
2. **选择合适模式**: I/O密集用threading/asyncio，CPU密集用multiprocessing
3. **监控资源使用**: 关注CPU、内存、网络使用情况
4. **处理失败任务**: 设置合理的超时和重试机制
5. **保存执行结果**: 便于后续分析和审计
6. **使用LangSmith追踪**: 帮助调试和性能优化

## 支持和反馈

如果遇到问题或有建议，请：

1. 查看日志文件 `concurrent_bigmodel.log`
2. 运行测试脚本 `python test_concurrent.py`
3. 检查网络连接和API密钥配置
4. 调整并发参数和超时设置