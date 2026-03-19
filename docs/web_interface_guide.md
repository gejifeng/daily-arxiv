# Web 界面使用指南

## 概述

Web 界面提供了一个现代化的响应式界面，用于查看每日 arXiv 论文摘要和趋势分析。

## 技术栈

- **后端**: Flask 3.0.2
- **前端**: Bootstrap 5, Chart.js
- **样式**: 自定义 CSS + Font Awesome
- **API**: RESTful API

## 目录结构

```
src/web/
├── app.py                    # Flask 应用主文件
├── templates/
│   └── index.html           # 主页模板
└── static/
    └── js/
        └── main.js          # 前端 JavaScript
```

## 快速启动

### 1. 安装依赖

```bash
pip install flask flask-cors markdown
```

或者使用 requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 开发模式（自动重载）
python src/web/app.py

# 或指定端口
FLASK_PORT=8080 python src/web/app.py
```

### 3. 访问界面

在浏览器中打开：`http://localhost:5000`

## 界面功能

### 1. 统计概览

页面顶部显示 4 个统计卡片：

- **论文数量**: 今日抓取的论文总数
- **总结数量**: 已生成的论文总结数
- **研究类别**: 涉及的研究领域数量
- **关键词数**: 提取的关键词总数

### 2. 趋势分析标签

#### 词云图

- 显示研究热点的可视化词云
- 字体大小表示关键词的重要程度
- 点击可查看大图

#### 研究热点

- 使用 TF-IDF 提取的关键词
- 显示权重和重要程度

#### 技术趋势

- LLM 分析生成的技术趋势洞察
- Markdown 格式渲染

#### 未来方向

- AI 预测的未来研究方向
- 基于当前论文的趋势分析

#### 研究思路

- LLM 生成的研究建议
- 适合研究人员参考

#### 分析总结

- 对整体分析结果的简洁总结
- 作为趋势分析页面的最后一个模块展示

### 3. 论文列表标签

#### 筛选和搜索

- **类别筛选**: 按研究领域过滤论文
- **搜索功能**: 按标题、作者、摘要搜索
- 实时过滤，无需刷新页面

#### 论文卡片

每个论文卡片包含：

- 论文标题（可点击查看详情）
- 作者列表
- 发布日期
- 研究类别标签
- 摘要预览
- 操作按钮：
  - 📄 查看详情
  - 🔗 arXiv 原文链接

#### 论文详情

点击"查看详情"后显示：

- 完整标题和作者
- 发布日期和更新日期
- 主类别和所有类别
- 完整摘要
- **AI 生成的论文总结** （如果可用）
- arXiv 原文链接
- PDF 下载链接

#### 分页

- 每页显示 10 篇论文
- 页码导航
- 显示总页数和当前页

## API 端点

### 基础信息

#### GET `/`
返回主页 HTML

#### GET `/api/stats`
返回统计信息

**响应示例**:
```json
{
  "papers_count": 20,
  "summaries_count": 20,
  "categories_count": 5,
  "keywords_count": 50,
  "last_update": "2024-01-15"
}
```

### 分析相关

#### GET `/api/analysis`
返回趋势分析数据

**响应示例**:
```json
{
  "keywords": [
    {"word": "transformer", "score": 0.85},
    {"word": "attention", "score": 0.72}
  ],
  "topics": [
    {"id": 1, "words": ["model", "training"], "score": 0.65}
  ],
  "llm_analysis": {
    "analysis_summary": "<h2>分析总结</h2><p>...</p>",
    "hotspots": "<h2>研究热点</h2><p>...</p>",
    "trends": "<h2>技术趋势</h2><p>...</p>",
    "future_directions": "<h2>未来方向</h2><p>...</p>",
    "research_ideas": "<h2>研究思路</h2><p>...</p>"
  },
  "statistics": {...}
}
```

#### GET `/api/wordcloud`
返回词云图 URL

**响应示例**:
```json
{
  "url": "/images/wordcloud_2024-01-15.png",
  "path": "data/analysis/wordcloud_2024-01-15.png"
}
```

### 论文相关

#### GET `/api/papers`
获取论文列表（支持分页和筛选）

**查询参数**:
- `page` (int): 页码，默认 1
- `per_page` (int): 每页数量，默认 10
- `category` (str): 类别筛选，可选

**响应示例**:
```json
{
  "papers": [...],
  "total": 20,
  "page": 1,
  "per_page": 10,
  "total_pages": 2
}
```

#### GET `/api/papers/<paper_id>`
获取单篇论文详情（包含总结）

**响应示例**:
```json
{
  "id": "2401.12345",
  "title": "论文标题",
  "authors": ["作者1", "作者2"],
  "abstract": "摘要...",
  "summary": "AI 生成的总结...",
  ...
}
```

#### GET `/api/summaries`
获取所有论文总结

**响应示例**:
```json
{
  "summaries": {
    "2401.12345": "论文总结...",
    ...
  }
}
```

#### GET `/api/categories`
获取所有类别及论文数量

**响应示例**:
```json
[
  {"name": "cs.AI", "count": 15},
  {"name": "cs.LG", "count": 12}
]
```

### 资源文件

#### GET `/images/<filename>`
获取图片文件（词云图等）

## 自定义配置

### 修改端口

编辑 `src/web/app.py`:

```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,  # 修改端口
        debug=True
    )
```

### 修改数据路径

编辑 `src/web/app.py` 中的路径常量：

```python
DATA_DIR = Path('data')
PAPERS_DIR = DATA_DIR / 'papers'
SUMMARIES_DIR = DATA_DIR / 'summaries'
ANALYSIS_DIR = DATA_DIR / 'analysis'
```

### 修改分页设置

编辑 `src/web/app.py` 中的 `get_papers` 函数：

```python
per_page = request.args.get('per_page', 20, type=int)  # 默认每页 20 篇
```

## 测试

运行测试脚本验证所有 API 端点：

```bash
# 先启动 Web 服务
python src/web/app.py

# 在另一个终端运行测试
python test_web.py
```

测试项目：
1. ✅ 主页加载
2. ✅ 统计信息 API
3. ✅ 趋势分析 API
4. ✅ 论文列表 API
5. ✅ 类别列表 API
6. ✅ 词云图 API

## 部署

### 生产环境部署

使用 Gunicorn:

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 src.web.app:app
```

使用 uWSGI:

```bash
pip install uwsgi

uwsgi --http 0.0.0.0:5000 --module src.web.app:app --processes 4
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /images/ {
        alias /path/to/daily-arxiv/data/analysis/;
    }
}
```

## 常见问题

### Q: 页面显示 "数据加载失败"

**A**: 检查以下几点：
1. 确保已运行论文抓取: `python main.py`
2. 确保 `data/papers/latest.json` 存在
3. 检查浏览器控制台错误信息
4. 查看 Flask 服务器日志

### Q: 词云图不显示

**A**: 
1. 确保已运行趋势分析: `python test_analyzer.py`
2. 检查 `data/analysis/` 目录是否有 `wordcloud_*.png` 文件
3. 确认 `/api/wordcloud` 端点返回正确 URL

### Q: 论文总结不显示

**A**:
1. 确保已运行总结生成: `python test_summarizer.py`
2. 检查 `data/summaries/latest.json` 是否存在
3. 确认论文 ID 匹配

### Q: 如何修改界面样式

**A**: 
- 编辑 `src/web/templates/index.html` 中的 `<style>` 部分
- 或创建独立的 CSS 文件放在 `static/css/` 目录

### Q: 如何添加新的 API 端点

**A**: 在 `src/web/app.py` 中添加新的路由:

```python
@app.route('/api/new-endpoint')
def new_endpoint():
    return jsonify({"data": "your data"})
```

## 下一步

- ✅ 完成 Web 界面开发
- ⏳ 添加定时调度功能（Step 6）
- ⏳ 添加邮件通知
- ⏳ 优化性能和缓存

## 支持

如有问题，请查看：
- [Flask 文档](https://flask.palletsprojects.com/)
- [Bootstrap 文档](https://getbootstrap.com/)
- [Chart.js 文档](https://www.chartjs.org/)
