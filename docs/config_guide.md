# 配置文件使用指南

本文档说明如何根据不同需求配置 `config/config.yaml`

## 🌍 语言配置（完整英文支持）

项目支持部署级语言切换，推荐在配置文件中显式设置：

```yaml
app:
  language: "zh"  # 可选: zh, en
```

当 `language: "en"` 时，以下内容会切换为英文输出：

- Web 界面文案
- LLM 提示词与分析文本
- 日志输出
- Markdown 报告内容

说明：该语言配置是全局生效的，适合统一部署环境（中文站点或英文站点）。

## 📋 配置场景

### 场景 1: 宽松搜索（推荐用于测试）

获取更多论文，不限制关键词：

```yaml
arxiv:
  categories:
    - "cs.AI"
    - "cs.LG"
  
  keywords: []  # 空列表 = 不过滤关键词
  
  max_results: 30  # 增加数量
  sort_by: "submittedDate"
  sort_order: "descending"
```

### 场景 2: 精确搜索（特定主题）

只获取特定关键词的论文：

```yaml
arxiv:
  categories:
    - "cs.LG"
  
  keywords:
    - "diffusion model"
    - "generative"
  
  max_results: 20
  sort_by: "relevance"  # 按相关性排序
  sort_order: "descending"
```

### 场景 3: 多领域综合

追踪多个研究领域：

```yaml
arxiv:
  categories:
    - "cs.AI"
    - "cs.LG"
    - "cs.CV"
    - "cs.CL"
  
  keywords: []  # 不限制关键词
  
  max_results: 50
  sort_by: "submittedDate"
  sort_order: "descending"
```

### 场景 4: LLM 专项追踪

专注于大语言模型研究：

```yaml
arxiv:
  categories:
    - "cs.CL"
    - "cs.AI"
    - "cs.LG"
  
  keywords:
    - "large language model"
    - "LLM"
    - "GPT"
    - "transformer"
    - "prompt"
  
  max_results: 25
  sort_by: "relevance"
  sort_order: "descending"
```

## 🔍 参数说明

### categories（类别）

**常用类别列表：**

| 类别代码 | 名称 | 说明 |
|---------|------|------|
| cs.AI | Artificial Intelligence | 人工智能 |
| cs.LG | Machine Learning | 机器学习 |
| cs.CV | Computer Vision | 计算机视觉 |
| cs.CL | Computation and Language | 自然语言处理 |
| cs.NE | Neural and Evolutionary Computing | 神经网络 |
| cs.RO | Robotics | 机器人 |
| stat.ML | Machine Learning (Statistics) | 统计机器学习 |

**完整列表**: https://arxiv.org/category_taxonomy

### keywords（关键词）

- **空列表 `[]`**: 不使用关键词过滤，只按类别搜索
- **单个关键词**: 只要标题或摘要中包含即可
- **多个关键词**: 任意一个匹配即可（OR 关系）

**注意**: 关键词越多，匹配条件越宽松！

### max_results（最大结果数）

- 建议值: 10-50
- 太小可能漏掉重要论文
- 太大可能包含不相关论文

### sort_by（排序方式）

- `submittedDate`: 按提交日期（推荐）
- `relevance`: 按相关性（需要有关键词时更有意义）
- `lastUpdatedDate`: 按更新日期

### sort_order（排序顺序）

- `descending`: 降序（新到旧，推荐）
- `ascending`: 升序（旧到新）

## 💡 最佳实践

### 1. 首次使用

```yaml
arxiv:
  categories: ["cs.AI", "cs.LG"]
  keywords: []  # 先不限制
  max_results: 30
  sort_by: "submittedDate"
  sort_order: "descending"
```

### 2. 日常使用

根据首次结果调整：
- 论文太多 → 增加关键词过滤
- 论文太少 → 删除关键词或增加类别
- 质量不高 → 调整为 `sort_by: "relevance"`

### 3. 专题研究

```yaml
arxiv:
  categories: ["cs.CV"]
  keywords: ["segmentation", "detection"]
  max_results: 20
  sort_by: "relevance"
```

## 🐛 常见问题

### Q: 为什么获取不到论文？

**原因可能是：**
1. 日期范围太短（修改 `main.py` 中的 `days_back`）
2. 关键词过滤太严格
3. 类别太少

**解决方法：**
```yaml
# 方案 1: 移除关键词限制
keywords: []

# 方案 2: 增加类别
categories: ["cs.AI", "cs.LG", "cs.CL"]

# 方案 3: 增加结果数量
max_results: 50
```

### Q: 论文质量不高，太多不相关的？

**解决方法：**
```yaml
# 1. 添加精确关键词
keywords: ["specific", "topic", "terms"]

# 2. 减少类别
categories: ["cs.LG"]  # 只保留最相关的

# 3. 按相关性排序
sort_by: "relevance"
```

### Q: 如何获取更长时间范围的论文？

修改 `main.py` 中的调用：
```python
papers = fetcher.fetch_papers(days_back=7)  # 过去7天
```

## 📝 配置模板

复制以下模板到 `config/config.yaml`：

```yaml
arxiv:
  # 【必填】研究领域类别
  categories:
    - "cs.AI"
    - "cs.LG"
  
  # 【可选】关键词过滤（空列表表示不过滤）
  keywords: []
  
  # 【推荐】每天获取的最大论文数量
  max_results: 30
  
  # 【推荐】排序方式
  sort_by: "submittedDate"
  sort_order: "descending"
```

## 🔄 实时调整

不需要重启程序，修改配置文件后直接运行即可：

```bash
# 修改 config/config.yaml
nano config/config.yaml

# 重新运行
python main.py
```
