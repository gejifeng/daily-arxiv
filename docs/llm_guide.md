# LLM 论文总结模块使用指南

## 📖 模块介绍

论文总结模块使用大语言模型（LLM）自动总结 arXiv 论文，支持多个主流 LLM 提供商。

## 🤖 支持的 LLM 提供商

| 提供商 | 说明 | 推荐模型 |
|-------|------|---------|
| **OpenAI** | GPT 系列，质量最高 | gpt-4o-mini, gpt-4o |
| **Google Gemini** | 性价比高，速度快 | gemini-1.5-flash |
| **Anthropic Claude** | 长文本能力强 | claude-3-5-sonnet |
| **DeepSeek** | 国产，价格便宜 | deepseek-chat |
| **vLLM** | 本地部署，完全免费 | 自定义模型 |

## ⚙️ 配置说明

### 0. 输出语言（完整英文支持）

在 `config/config.yaml` 中设置：

```yaml
app:
  language: "zh"  # 可选: zh, en
```

当设置为 `en` 时，LLM 相关提示词、日志与分析报告将统一输出英文（并与 Web 界面语言配置保持一致）。

### 1. 选择 LLM 提供商

在 `config/config.yaml` 中设置：

```yaml
llm:
  provider: "openai"  # 可选: openai, gemini, claude, deepseek, vllm
```

### 2. 配置 API Key

在 `.env` 文件中设置对应的 API Key：

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Google Gemini
GEMINI_API_KEY=...

# Anthropic Claude
CLAUDE_API_KEY=sk-ant-...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# vLLM (本地部署)
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL=your-model-name
```

### 3. 详细配置选项

```yaml
llm:
  provider: "openai"
  
  openai:
    api_key: ""  # 留空，从 .env 读取
    model: "gpt-4o-mini"
    base_url: ""  # 可选，用于代理
    temperature: 0.7
    max_tokens: 1500
```

## 🚀 快速开始

### 方案 1: OpenAI (推荐)

1. **获取 API Key**
   - 访问: https://platform.openai.com/api-keys
   - 创建新的 API Key

2. **配置**
   ```yaml
   # config/config.yaml
   llm:
     provider: "openai"
     openai:
       model: "gpt-4o-mini"  # 便宜快速
       temperature: 0.7
       max_tokens: 1500
   ```
   
   ```bash
   # .env
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **运行**
   ```bash
   python main.py
   ```

### 方案 2: Google Gemini (免费额度大)

1. **获取 API Key**
   - 访问: https://makersuite.google.com/app/apikey
   - 创建 API Key

2. **配置**
   ```yaml
   # config/config.yaml
   llm:
     provider: "gemini"
     gemini:
       model: "gemini-1.5-flash"
       temperature: 0.7
       max_tokens: 1500
   ```
   
   ```bash
   # .env
   GEMINI_API_KEY=your-key-here
   ```

### 方案 3: Claude

1. **获取 API Key**
   - 访问: https://console.anthropic.com/
   - 创建 API Key

2. **配置**
   ```yaml
   llm:
     provider: "claude"
     claude:
       model: "claude-3-5-sonnet-20241022"
       temperature: 0.7
   ```
   
   ```bash
   # .env
   CLAUDE_API_KEY=sk-ant-your-key-here
   ```

### 方案 4: DeepSeek (国产)

1. **获取 API Key**
   - 访问: https://platform.deepseek.com/
   - 注册并创建 API Key

2. **配置**
   ```yaml
   llm:
     provider: "deepseek"
     deepseek:
       model: "deepseek-chat"
       base_url: "https://api.deepseek.com/v1"
   ```
   
   ```bash
   # .env
   DEEPSEEK_API_KEY=sk-your-key-here
   ```

### 方案 5: vLLM (本地部署)

1. **启动 vLLM 服务**
   ```bash
   python -m vllm.entrypoints.openai.api_server \
     --model meta-llama/Llama-2-7b-chat-hf \
     --port 8000
   ```

2. **配置**
   ```yaml
   llm:
     provider: "vllm"
     vllm:
       model: "meta-llama/Llama-2-7b-chat-hf"
       base_url: "http://localhost:8000/v1"
       api_key: "EMPTY"
   ```

## 📊 功能特性

### 1. 单篇论文总结

```python
from src.summarizer.paper_summarizer import PaperSummarizer

summarizer = PaperSummarizer(config)
summarized_paper = summarizer.summarize_paper(paper)

print(summarized_paper['summary'])
```

### 2. 批量论文总结

```python
summarized_papers = summarizer.summarize_papers(papers)
```

### 3. 生成每日报告

```python
report = summarizer.generate_daily_report(summarized_papers)
print(report)  # Markdown 格式的报告
```

## 🧪 测试

```bash
# 测试 LLM 连接和功能
python test_summarizer.py
```

测试脚本会：
1. 测试 LLM 客户端创建
2. 测试简单文本生成
3. 测试论文总结功能
4. （可选）对比不同 LLM 提供商

## 💰 成本对比

| 提供商 | 输入价格 | 输出价格 | 备注 |
|-------|---------|---------|------|
| OpenAI gpt-4o-mini | $0.15/1M tokens | $0.6/1M tokens | 性价比最高 |
| Gemini Flash | 免费 | 免费 | 有配额限制 |
| Claude Sonnet | $3/1M tokens | $15/1M tokens | 质量很高 |
| DeepSeek | ¥1/1M tokens | ¥2/1M tokens | 非常便宜 |
| vLLM | 免费 | 免费 | 需要 GPU |

**估算**: 总结 20 篇论文约消耗 ~30K tokens，成本：
- OpenAI gpt-4o-mini: ~$0.02
- Gemini: 免费
- DeepSeek: ~¥0.06
- vLLM: 免费

## 🔧 高级配置

### 自定义提示词

修改 `src/summarizer/paper_summarizer.py`：

```python
SYSTEM_PROMPT = """你的自定义系统提示词..."""

USER_PROMPT_TEMPLATE = """你的自定义用户提示词...
标题：{title}
..."""
```

### 调整生成参数

```yaml
llm:
  openai:
    temperature: 0.5  # 降低随机性，更确定的输出
    max_tokens: 2000  # 增加输出长度
```

### 使用代理

```yaml
llm:
  openai:
    base_url: "https://your-proxy.com/v1"
```

或在 `.env` 中：
```bash
OPENAI_BASE_URL=https://your-proxy.com/v1
```

## 📝 输出格式

### 总结数据

保存在 `data/summaries/summaries_YYYY-MM-DD.json`：

```json
{
  "id": "2310.12345",
  "title": "论文标题",
  "summary": "这是一篇关于...的论文，主要创新点是...",
  "summarized_at": "2024-10-13T10:30:00",
  ...
}
```

### 每日报告

保存在 `data/summaries/report_YYYY-MM-DD.md`，Markdown 格式。

## 🐛 常见问题

### Q1: API Key 错误

**错误信息**: `ValueError: XXX API Key 未设置`

**解决方法**:
```bash
# 1. 检查 .env 文件
cat .env

# 2. 确认 API Key 格式正确
# OpenAI: sk-...
# Claude: sk-ant-...
# Gemini: AI...

# 3. 重新加载环境变量
source .env  # 或重启程序
```

### Q2: 速率限制

**错误信息**: `Rate limit exceeded`

**解决方法**:
- 降低并发数（目前是顺序处理）
- 升级 API 套餐
- 切换到其他提供商
- 使用本地 vLLM

### Q3: 连接超时

**错误信息**: `Connection timeout`

**解决方法**:
- 检查网络连接
- 使用代理
- 切换提供商

### Q4: vLLM 连接失败

**错误信息**: `Failed to connect to vLLM`

**解决方法**:
```bash
# 1. 确认 vLLM 服务正在运行
curl http://localhost:8000/v1/models

# 2. 检查配置
# config.yaml 中的 base_url 是否正确

# 3. 查看 vLLM 日志
```

### Q5: 中文乱码

**解决方法**:
- 确保文件以 UTF-8 编码保存
- 检查终端编码设置

## 🎯 最佳实践

### 1. 选择合适的模型

- **快速原型**: gemini-1.5-flash (免费)
- **日常使用**: gpt-4o-mini (便宜)
- **高质量**: claude-3-5-sonnet
- **国内网络**: deepseek-chat
- **隐私优先**: vLLM (本地)

### 2. 优化成本

```python
# 只总结重要论文
important_papers = [p for p in papers if is_important(p)]
summarized = summarizer.summarize_papers(important_papers)

# 或者使用更便宜的模型
config['llm']['provider'] = 'gemini'
```

### 3. 错误处理

程序已内置错误处理，失败的论文会标记 `summary_error=True`。

## 📚 相关文档

- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [Google Gemini 文档](https://ai.google.dev/docs)
- [Anthropic Claude 文档](https://docs.anthropic.com/)
- [DeepSeek 文档](https://platform.deepseek.com/api-docs/)
- [vLLM 文档](https://docs.vllm.ai/)
