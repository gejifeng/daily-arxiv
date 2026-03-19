"""
Flask Web 应用

展示 arXiv 论文分析结果
"""
import os
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, jsonify, request, send_from_directory
# from flask_cors import CORS  # 暂时注释，本地开发不需要
import markdown

from src.utils import load_config, load_json, get_language


# 创建 Flask 应用
# 指定模板和静态文件路径为项目根目录
app = Flask(
    __name__,
    template_folder=str(project_root / 'src' / 'web' / 'templates'),
    static_folder=str(project_root / 'static'),
    static_url_path='/static'
)
# CORS(app)  # 暂时注释，本地开发不需要

# 加载配置
config = load_config()
web_config = config.get('web', {})
language = get_language(config)

WEB_I18N = {
    'zh': {
        'html_lang': 'zh-CN',
        'title_default': 'Daily arXiv - AI Research Tracker',
        'description_default': '每日追踪最新的 AI 研究论文',
        'error_no_analysis': '没有找到分析数据',
        'error_no_papers': '没有找到论文数据',
        'error_no_summaries': '没有找到总结数据',
        'error_paper_not_found': '论文不存在',
        'web_start': 'Daily arXiv Web 服务启动',
        'access_url': '访问地址',
        'api_doc': 'API 文档',
        'stop_hint': '按 Ctrl+C 停止服务',
    },
    'en': {
        'html_lang': 'en-US',
        'title_default': 'Daily arXiv - AI Research Tracker',
        'description_default': 'Track the latest AI research papers daily',
        'error_no_analysis': 'Analysis data not found',
        'error_no_papers': 'Paper data not found',
        'error_no_summaries': 'Summary data not found',
        'error_paper_not_found': 'Paper not found',
        'web_start': 'Daily arXiv Web Service Started',
        'access_url': 'Access URL',
        'api_doc': 'API docs',
        'stop_hint': 'Press Ctrl+C to stop the service',
    }
}


def t(key: str) -> str:
    return WEB_I18N[language].get(key, key)

app.config['TITLE'] = web_config.get('title', t('title_default'))
app.config['DESCRIPTION'] = web_config.get('description', t('description_default'))


@app.route('/')
def index():
    """主页"""
    return render_template('index.html',
                         title=app.config['TITLE'],
                         description=app.config['DESCRIPTION'],
                         language=language,
                         html_lang=t('html_lang'))


@app.route('/api/analysis')
def get_analysis():
    """获取趋势分析数据"""
    try:
        # 加载最新的分析数据
        analysis_data = load_json('data/analysis/latest.json')
        
        if not analysis_data:
            return jsonify({'error': t('error_no_analysis')}), 404
        
        # 处理 LLM 分析的 Markdown 内容
        llm_analysis = analysis_data.get('llm_analysis', {})
        for key in ['analysis_summary', 'hotspots', 'trends', 'future_directions', 'research_ideas']:
            if key in llm_analysis and llm_analysis[key]:
                # 将 Markdown 转换为 HTML
                llm_analysis[f'{key}_html'] = markdown.markdown(
                    llm_analysis[key],
                    extensions=['tables', 'fenced_code', 'nl2br']
                )
        
        return jsonify(analysis_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/papers')
def get_papers():
    """获取论文列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category', '')
        
        # 加载论文数据
        papers_data = load_json('data/papers/latest.json')
        
        if not papers_data:
            return jsonify({'error': t('error_no_papers')}), 404
        
        papers = papers_data.get('papers', [])
        
        # 按类别过滤
        if category:
            papers = [p for p in papers if category in p.get('categories', [])]
        
        # 分页
        total = len(papers)
        start = (page - 1) * per_page
        end = start + per_page
        papers_page = papers[start:end]
        
        return jsonify({
            'papers': papers_page,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'date': papers_data.get('date')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/papers/<paper_id>')
def get_paper_detail(paper_id):
    """获取论文详情（包括总结）"""
    try:
        # 加载论文数据
        papers_data = load_json('data/papers/latest.json')
        papers = papers_data.get('papers', [])
        
        # 查找论文
        paper = None
        for p in papers:
            if p.get('id') == paper_id:
                paper = p
                break
        
        if not paper:
            return jsonify({'error': t('error_paper_not_found')}), 404
        
        # 加载总结数据
        summaries_data = load_json('data/summaries/latest.json')
        if summaries_data:
            summaries = summaries_data.get('summaries', [])
            # 查找对应的总结
            for summary in summaries:
                if summary.get('paper_id') == paper_id:
                    paper['summary'] = summary.get('summary')
                    break
        
        return jsonify(paper)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/summaries')
def get_summaries():
    """获取论文总结列表"""
    try:
        summaries_data = load_json('data/summaries/latest.json')
        
        if not summaries_data:
            return jsonify({'error': t('error_no_summaries')}), 404
        
        return jsonify(summaries_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/categories')
def get_categories():
    """获取所有类别"""
    try:
        papers_data = load_json('data/papers/latest.json')
        
        if not papers_data:
            return jsonify({'error': t('error_no_papers')}), 404
        
        papers = papers_data.get('papers', [])
        
        # 统计类别
        categories = {}
        for paper in papers:
            for cat in paper.get('categories', []):
                categories[cat] = categories.get(cat, 0) + 1
        
        # 转换为列表并排序
        category_list = [
            {'name': cat, 'count': count}
            for cat, count in categories.items()
        ]
        category_list.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify(category_list)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    try:
        # 加载数据
        papers_data = load_json('data/papers/latest.json')
        summaries_data = load_json('data/summaries/latest.json')
        analysis_data = load_json('data/analysis/latest.json')
        
        stats = {
            'papers_count': len(papers_data.get('papers', [])) if papers_data else 0,
            'summaries_count': len(summaries_data.get('summaries', [])) if summaries_data else 0,
            'analysis_available': analysis_data is not None,
            'last_update': papers_data.get('date') if papers_data else None
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/images/<path:filename>')
def serve_image(filename):
    """提供图片文件"""
    analysis_dir = project_root / 'data' / 'analysis'
    return send_from_directory(str(analysis_dir), filename)


@app.route('/api/wordcloud')
def get_wordcloud():
    """获取词云图片路径"""
    try:
        analysis_data = load_json('data/analysis/latest.json')
        
        if not analysis_data:
            return jsonify({'error': t('error_no_analysis')}), 404
        
        wordcloud_path = analysis_data.get('wordcloud_path', '')
        
        # 转换为相对路径
        if wordcloud_path:
            filename = os.path.basename(wordcloud_path)
            wordcloud_url = f'/images/{filename}'
        else:
            wordcloud_url = None
        
        return jsonify({
            'url': wordcloud_url,
            'path': wordcloud_path
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """运行 Web 服务"""
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    debug = web_config.get('debug', True)
    
    print("\n" + "=" * 60)
    print(f"🌐 {t('web_start')}")
    print("=" * 60)
    print(f"{t('access_url')}: http://localhost:{port}")
    print(f"{t('api_doc')}: http://localhost:{port}/api/stats")
    print("=" * 60)
    print(f"{t('stop_hint')}\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
