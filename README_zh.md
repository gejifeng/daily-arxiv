# Daily arXiv - AI Research Tracker 📚🤖

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![arXiv](https://img.shields.io/badge/arXiv-cs.AI-b31b1b.svg)](https://arxiv.org/list/cs.AI/recent)

[English](README.md) | **中文文档**

每日自动追踪 arXiv 上最新的 AI 研究论文，使用 LLM 进行智能总结，并生成研究趋势分析报告。

## ✨ 功能特性

### 核心功能

- 🔍 **智能爬取**: 每天自动从 arXiv 获取指定领域的最新论文
  - 支持多研究领域（cs.AI, cs.LG, cs.CV等）
  - 关键词过滤
  - TF-IDF 智能筛选

- 🤖 **多模型总结**: 使用 LLM 对论文进行智能总结
  - 支持 5 种 LLM 提供商：OpenAI、Gemini、Claude、DeepSeek、vLLM
  - 中英文双语总结
  - 并发处理提升效率

- 📊 **趋势分析**: 深度分析研究热点和技术趋势
  - TF-IDF 关键词提取
  - LDA 主题建模
  - 词云可视化
  - LLM 深度分析（研究热点、技术趋势、未来方向、创新研究想法、分析总结）

- 🌐 **Web 界面**: 现代化响应式 Web 界面
  - Bootstrap 5 设计
  - 实时数据展示
  - 论文详情查看
  - 分页和筛选

- 🌍 **完整英文支持**: 提供完整英文使用体验
  - 界面文案支持英文显示
  - 日志、提示词与分析报告支持英文输出
  - 中英文文档保持同步

- ⏰ **定时调度**: 支持多种调度方式
  - APScheduler 调度器（推荐）
  - Linux Cron 任务
  - Systemd 系统服务

- 📧 **邮件通知**: 任务执行状态邮件通知
  - 美观的 HTML 邮件模板
  - 成功/失败分别通知
  - 详细统计信息

## 📸 界面预览

![alt text](resources/image0.png)![alt text](resources/image1.png)![alt text](resources/image2.png)

## 🚀 快速开始

### 前置要求

- Python 3.12+
- Conda（推荐）或 virtualenv
- LLM API Key（OpenAI/Gemini/Claude/DeepSeek/vLLM）

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/daily-arxiv.git
cd daily-arxiv
```

### 2. 创建虚拟环境

```bash
# 使用 Conda（推荐）
conda create -n daily-arxiv python=3.12 -y
conda activate daily-arxiv

# 或使用 venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install uv
uv pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件
nano .env
```

添加你的 API Key：

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Google Gemini
GEMINI_API_KEY=...

# Anthropic Claude
ANTHROPIC_API_KEY=...

# DeepSeek
DEEPSEEK_API_KEY=...

# vLLM (本地部署)
VLLM_API_KEY=EMPTY

# 邮件通知（可选）
EMAIL_PASSWORD=your-app-password
```

### 5. 配置 config.yaml

编辑 `config/config.yaml`：

```yaml
# 应用语言（部署级）：zh 或 en
app:
  language: "zh"

# 研究领域
arxiv:
  categories:
    - "cs.AI"  # 人工智能
    - "cs.LG"  # 机器学习
  
  keywords:
    - "large language model"
    - "transformer"
  
  max_results: 20

# LLM 提供商
llm:
  provider: "vllm"  # openai, gemini, claude, deepseek, vllm

# 调度配置
scheduler:
  enabled: true
  run_time: "09:00"
  timezone: "Asia/Shanghai"
```

### 6. 运行测试

```bash
# 测试论文抓取
python test/test_fetcher.py

# 测试 LLM 总结
python test/test_summarizer.py

# 测试趋势分析
python test/test_analyzer.py

# 测试 Web 服务
python test/test_web.py

# 测试调度器
python test/test_scheduler.py
```

### 7. 运行完整流程

```bash
# 手动运行一次
python main.py
```

### 8. 启动 Web 服务

```bash
# 开发模式
python src/web/app.py

# 访问 http://localhost:5000
```

### 9. 启动定时调度

```bash
# 使用启动脚本（推荐）
./deploy/start.sh

# 或直接运行
python scheduler.py
```

`deploy/start.sh` 现在支持：
- 启动时询问是否立即初始化环境（可跳过）。
- Conda/venv 环境初始化。
- 自动扫描已有环境，并让你选择“使用已有”或“创建新的”。
- 菜单中直接执行 systemd 一键部署（选项 8）。

### 10. 以 systemd 服务方式部署（Linux）

```bash
# 一键部署将会：
# 1) 选择 Conda 或 venv
# 2) 选择使用已有环境或创建新环境
# 3) 自动安装依赖
# 4) 自动生成本机 service
# 5) 启用并启动服务
bash deploy/deploy_services.sh
```

部署脚本内置常见异常检查（例如 Web 端口被占用、系统命令缺失、Python 环境不可用），出现问题会明确报错并退出。

### 11. 卸载 systemd 服务（Linux）

```bash
# 停止、禁用、删除服务文件并重载 systemd
bash deploy/uninstall_services.sh
```

访问 http://localhost:5000 查看结果。

## � 项目结构

```
daily-arxiv/
├── config/
│   └── config.yaml              # 主配置文件
├── src/
│   ├── crawler/
│   │   └── arxiv_fetcher.py    # arXiv 论文爬取
│   ├── summarizer/
│   │   ├── base_llm_client.py  # LLM 基类
│   │   ├── openai_client.py    # OpenAI 客户端
│   │   ├── gemini_client.py    # Gemini 客户端
│   │   ├── claude_client.py    # Claude 客户端
│   │   ├── deepseek_client.py  # DeepSeek 客户端
│   │   ├── vllm_client.py      # vLLM 客户端
│   │   ├── llm_factory.py      # LLM 工厂
│   │   └── paper_summarizer.py # 论文总结器
│   ├── analyzer/
│   │   └── trend_analyzer.py   # 趋势分析
│   ├── web/
│   │   ├── app.py             # Flask Web 应用
│   │   └── templates/
│   │       └── index.html     # Web 界面
│   ├── notifier/
│   │   └── email_notifier.py  # 邮件通知
│   └── utils.py               # 工具函数
├── static/
│   └── js/
│       └── main.js            # 前端 JavaScript
├── data/                      # 数据存储目录
│   ├── papers/               # 论文 JSON 数据
│   ├── summaries/            # 总结 JSON 数据
│   └── analysis/             # 分析结果和词云图
├── logs/                     # 日志文件
├── deploy/                   # 部署脚本
│   ├── start.sh             # 本地交互式启动脚本
│   ├── deploy_services.sh   # Linux 一键部署脚本
│   ├── daily-arxiv-scheduler.service # 调度器 systemd 模板
│   ├── daily-arxiv-web.service       # Web systemd 模板
│   └── crontab.example      # Cron 示例
├── docs/                     # 文档
│   ├── arxiv_fetcher_guide.md
│   ├── trend_analyzer_guide.md
│   ├── web_interface_guide.md
│   └── scheduler_guide.md
├── main.py                   # 主程序入口
├── scheduler.py              # APScheduler 调度器
├── test_*.py                # 测试脚本
├── requirements.txt         # Python 依赖
├── .env.example            # 环境变量示例
└── README.md               # 项目说明
```

## ⚙️ 配置说明

### arXiv 类别代码

常用的计算机科学类别：
- `cs.AI` - Artificial Intelligence (人工智能)
- `cs.LG` - Machine Learning (机器学习)
- `cs.CV` - Computer Vision (计算机视觉)
- `cs.CL` - Computation and Language (自然语言处理)
- `cs.NE` - Neural and Evolutionary Computing (神经网络)
- `stat.ML` - Machine Learning (统计机器学习)

更多类别请参考：https://arxiv.org/category_taxonomy

### LLM 提供商

支持以下 LLM 提供商：
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Gemini**: Gemini
- **Anthropic**: Claude
- **Deepseek**: Deepseek
- **vllm**: 本地运行的开源模型(OpenAI兼容API)

## 📝 开发计划

- [x] 项目结构搭建 ✅
- [x] arXiv 论文爬取功能 ✅
- [x] LLM 论文总结功能 ✅
  - 支持 OpenAI, Gemini, Claude, DeepSeek, vLLM
- [x] 趋势分析功能 ✅
  - 关键词提取、主题建模、词云生成
  - LLM 深度分析（研究热点、技术趋势、未来方向、创新研究想法、分析总结）
- [x] 完整英文支持 ✅
  - 界面文案、日志、提示词、分析报告与文档均已支持英文
- [x] Web 界面开发
- [x] 定时调度功能
- [x] 测试和优化
- [ ] 美化web页面
- [ ] 添加微信公众号功能

## 🧪 测试

```bash
# 测试论文爬取功能
python test/test_fetcher.py

# 测试论文总结功能
python test/test_summarizer.py

# 测试趋势分析功能
python test/test_analyzer.py

# 运行完整流程
python main.py
```

## 📊 生成的文件

```
data/
├── papers/
│   ├── papers_YYYY-MM-DD.json     # 每日论文数据
│   └── latest.json                 # 最新论文数据
├── summaries/
│   ├── summaries_YYYY-MM-DD.json  # 每日论文总结
│   └── latest.json                 # 最新总结数据
└── analysis/
    ├── wordcloud_YYYY-MM-DD.png   # 词云图
    ├── analysis_YYYY-MM-DD.json   # 分析结果
    ├── report_YYYY-MM-DD.md       # Markdown 报告
    └── latest.json                 # 最新分析数据
```

## 📖 文档

- 已完成中英文文档与界面说明同步，英文支持完整可用。
- [论文爬取模块指南](docs/arxiv_fetcher_guide.md)
- [LLM 总结模块指南](docs/llm_guide.md)
- [配置说明](docs/config_guide.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
