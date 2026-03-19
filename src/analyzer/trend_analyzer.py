"""
趋势分析器 / Trend analyzer

分析论文集合，生成 / Analyze paper sets and generate:
1. 词云图
2. 研究热点分析
3. 趋势预测
4. 研究创新点建议
"""
import logging
import json
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from collections import Counter
import re

# 词云和可视化 / Word cloud and visualization
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 文本处理 / Text processing
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
from nltk.corpus import stopwords

from src.utils import save_json, get_date_string, get_language, pick_text


class TrendAnalyzer:
    """趋势分析器 / Trend analyzer"""
    
    def __init__(self, config: Dict[str, Any], llm_client=None):
        """初始化
        
        Args:
            config: 配置字典
            llm_client: LLM 客户端（用于生成分析报告）
        """
        self.config = config
        self.language = get_language(config)
        self.llm_client = llm_client
        self.logger = logging.getLogger('daily_arxiv.analyzer')
        self.text = lambda zh, en: pick_text(self.config, zh, en)
        
        # 下载必要的 NLTK 数据 / Download required NLTK resources
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            self.logger.info(self.text("下载 NLTK stopwords...", "Downloading NLTK stopwords..."))
            nltk.download('stopwords', quiet=True)
        
        self.stop_words = set(stopwords.words('english'))
        # 添加自定义停用词 / Add custom stop words
        self.stop_words.update([
            'paper', 'study', 'research', 'approach', 'method', 'propose',
            'propose', 'present', 'show', 'demonstrate', 'arxiv', 'preprint',
            'et', 'al', 'also', 'based', 'using', 'used', 'use', 'new',
            'work', 'results', 'result', 'performance', 'model', 'models'
        ])
    
    def analyze(self, papers: List[Dict[str, Any]], summaries: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行完整的趋势分析
        
        Args:
            papers: 论文列表
            summaries: 论文总结列表（可选）
            
        Returns:
            分析结果字典
        """
        self.logger.info("=" * 60)
        self.logger.info(self.text("🔍 开始趋势分析", "🔍 Starting trend analysis"))
        self.logger.info(self.text(f"分析论文数量: {len(papers)}", f"Number of papers analyzed: {len(papers)}"))
        self.logger.info("=" * 60)
        
        if not papers:
            self.logger.warning(self.text("没有论文可分析", "No papers available for analysis"))
            return {}
        
        # 1. 提取关键词和主题 / Extract keywords and topics
        self.logger.info(self.text("\n步骤 1: 提取关键词和主题...", "\nStep 1: Extracting keywords and topics..."))
        keywords = self._extract_keywords(papers)
        topics = self._extract_topics(papers)
        
        # 2. 生成词云 / Generate word cloud
        self.logger.info(self.text("\n步骤 2: 生成词云...", "\nStep 2: Generating word cloud..."))
        wordcloud_path = self._generate_wordcloud(papers)
        
        # 3. 统计分析 / Compute statistics
        self.logger.info(self.text("\n步骤 3: 统计分析...", "\nStep 3: Computing statistics..."))
        statistics = self._generate_statistics(papers, summaries)
        
        # 4. 使用 LLM 生成深度分析 / Use LLM for in-depth analysis
        self.logger.info(self.text("\n步骤 4: 生成深度分析报告...", "\nStep 4: Generating in-depth analysis..."))
        llm_analysis = self._generate_llm_analysis(papers, summaries, keywords, topics)
        
        # 组合所有分析结果 / Combine all analysis outputs
        analysis_result = {
            'date': get_date_string(),
            'paper_count': len(papers),
            'keywords': keywords,
            'topics': topics,
            'statistics': statistics,
            'wordcloud_path': wordcloud_path,
            'llm_analysis': llm_analysis,
            'generated_at': datetime.now().isoformat()
        }
        
        # 保存分析结果 / Save analysis artifacts
        self._save_analysis(analysis_result)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(self.text("✅ 趋势分析完成", "✅ Trend analysis completed"))
        self.logger.info("=" * 60)
        
        return analysis_result
    
    def _extract_keywords(self, papers: List[Dict[str, Any]], top_n: int = 50) -> List[Dict[str, Any]]:
        """提取关键词（使用 TF-IDF）
        
        Args:
            papers: 论文列表
            top_n: 返回前 N 个关键词
            
        Returns:
            关键词列表，包含词和权重
        """
        # 合并所有论文的标题和摘要 / Merge titles and abstracts
        texts = []
        for paper in papers:
            text = paper['title'] + ' ' + paper['abstract']
            texts.append(text)
        
        # 使用 TF-IDF 提取关键词 / Extract keywords with TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=top_n,
            stop_words=list(self.stop_words),
            ngram_range=(1, 2),  # 包括单词和二元组
            min_df=2,  # 至少出现在2篇论文中
            max_df=0.8  # 最多出现在80%的论文中
        )
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # 计算每个词的平均 TF-IDF 分数 / Compute average TF-IDF score per term
        avg_scores = tfidf_matrix.mean(axis=0).A1
        keyword_scores = list(zip(feature_names, avg_scores))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        keywords = [
            {'keyword': kw, 'score': float(score)}
            for kw, score in keyword_scores[:top_n]
        ]
        
        self.logger.info(self.text(f"✓ 提取了 {len(keywords)} 个关键词", f"✓ Extracted {len(keywords)} keywords"))
        self.logger.info(f"  Top 10: {', '.join([k['keyword'] for k in keywords[:10]])}")
        
        return keywords
    
    def _extract_topics(self, papers: List[Dict[str, Any]], n_topics: int = 5) -> List[Dict[str, Any]]:
        """提取主题（使用 LDA）
        
        Args:
            papers: 论文列表
            n_topics: 主题数量
            
        Returns:
            主题列表
        """
        # 合并所有论文的标题和摘要
        texts = []
        for paper in papers:
            text = paper['title'] + ' ' + paper['abstract']
            texts.append(text)
        
        # 使用 CountVectorizer
        vectorizer = CountVectorizer(
            max_features=1000,
            stop_words=list(self.stop_words),
            min_df=2,
            max_df=0.8
        )
        
        doc_term_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # 使用 LDA 提取主题 / Extract topics with LDA
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=20
        )
        lda.fit(doc_term_matrix)
        
        # 提取每个主题的关键词 / Extract top terms per topic
        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_indices]
            topic_weight = topic[top_indices]
            
            topics.append({
                'topic_id': topic_idx + 1,
                'keywords': top_words,
                'weights': [float(w) for w in topic_weight]
            })
        
        self.logger.info(self.text(f"✓ 提取了 {len(topics)} 个主题", f"✓ Extracted {len(topics)} topics"))
        for i, topic in enumerate(topics, 1):
            self.logger.info(self.text(f"  主题 {i}: {', '.join(topic['keywords'][:5])}", f"  Topic {i}: {', '.join(topic['keywords'][:5])}"))
        
        return topics
    
    def _generate_wordcloud(self, papers: List[Dict[str, Any]]) -> str:
        """生成词云图
        
        Args:
            papers: 论文列表
            
        Returns:
            词云图片路径
        """
        # 合并所有文本 / Merge all texts
        text = ' '.join([
            paper['title'] + ' ' + paper['abstract']
            for paper in papers
        ])
        
        # 清理文本 / Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # 生成词云 / Generate word cloud
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color='white',
            stopwords=self.stop_words,
            max_words=100,
            relative_scaling=0.5,
            colormap='viridis',
            min_font_size=10
        ).generate(text)
        
        # 保存图片 / Save image
        output_dir = Path('data/analysis')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = get_date_string()
        wordcloud_path = f"data/analysis/wordcloud_{date_str}.png"
        
        # 创建图表 / Create figure
        plt.figure(figsize=(16, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Research Trends Word Cloud - {date_str}', fontsize=20, pad=20)
        plt.tight_layout(pad=0)
        
        # 保存 / Save figure
        plt.savefig(wordcloud_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.logger.info(self.text(f"✓ 词云已保存: {wordcloud_path}", f"✓ Word cloud saved: {wordcloud_path}"))
        
        return wordcloud_path
    
    def _generate_statistics(self, papers: List[Dict[str, Any]], 
                           summaries: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成统计信息
        
        Args:
            papers: 论文列表
            summaries: 论文总结列表
            
        Returns:
            统计信息字典
        """
        # 类别统计 / Category stats
        category_counts = Counter()
        for paper in papers:
            for category in paper.get('categories', []):
                category_counts[category] += 1
        
        # 作者统计 / Author stats
        author_counts = Counter()
        for paper in papers:
            for author in paper.get('authors', []):
                author_counts[author] += 1
        
        # 高频词统计 / High-frequency words
        word_counts = Counter()
        for paper in papers:
            title_words = paper['title'].lower().split()
            abstract_words = paper['abstract'].lower().split()
            for word in title_words + abstract_words:
                word = re.sub(r'[^\w]', '', word)
                if len(word) > 3 and word not in self.stop_words:
                    word_counts[word] += 1
        
        # 时间分布 / Time distribution
        time_distribution = Counter()
        for paper in papers:
            published = paper.get('published', '')
            if published:
                date = published.split('T')[0]
                time_distribution[date] += 1
        
        statistics = {
            'total_papers': len(papers),
            'total_authors': len(author_counts),
            'total_categories': len(category_counts),
            'category_distribution': dict(category_counts.most_common(10)),
            'top_authors': dict(author_counts.most_common(10)),
            'top_words': dict(word_counts.most_common(30)),
            'time_distribution': dict(sorted(time_distribution.items())),
            'prolific_authors': {k: v for k, v in author_counts.items() if v >= 2}
        }
        
        return statistics
    
    def _generate_llm_analysis(self, papers: List[Dict[str, Any]], 
                              summaries: List[Dict[str, Any]] = None,
                              keywords: List[Dict[str, Any]] = None,
                              topics: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用 LLM 生成深度分析
        
        Args:
            papers: 论文列表
            summaries: 论文总结列表
            keywords: 关键词列表
            topics: 主题列表
            
        Returns:
            LLM 分析结果
        """
        if not self.llm_client:
            self.logger.warning(self.text("未提供 LLM 客户端，跳过深度分析", "LLM client not provided, skipping in-depth analysis"))
            return {
                'hotspots': pick_text(self.config, '需要 LLM 客户端', 'LLM client is required'),
                'trends': pick_text(self.config, '需要 LLM 客户端', 'LLM client is required'),
                'future_directions': pick_text(self.config, '需要 LLM 客户端', 'LLM client is required'),
                'research_ideas': pick_text(self.config, '需要 LLM 客户端', 'LLM client is required')
            }
        
        # 准备论文摘要信息 / Prepare paper summary block
        papers_summary = []
        for i, paper in enumerate(papers[:30], 1):  # 限制在前30篇 / Limit to first 30 papers
            summary_text = ""
            if summaries and i-1 < len(summaries):
                summary = summaries[i-1].get('summary', {})
                if isinstance(summary, dict):
                    summary_text = self.text(
                        f"\n  关键创新: {summary.get('key_innovation', '')}\n  主要方法: {summary.get('main_method', '')}",
                        f"\n  Key innovation: {summary.get('key_innovation', '')}\n  Main method: {summary.get('main_method', '')}"
                    )
            
            papers_summary.append(
                f"{i}. {paper['title']}\n"
                + self.text(f"  类别: {', '.join(paper['categories'][:3])}", f"  Categories: {', '.join(paper['categories'][:3])}")
                + f"{summary_text}"
            )
        
        # 准备关键词信息 / Prepare keyword block
        top_keywords = [kw['keyword'] for kw in (keywords[:30] if keywords else [])]
        
        # 准备主题信息 / Prepare topic block
        topic_descriptions = []
        if topics:
            for topic in topics:
                topic_descriptions.append(
                    self.text(
                        f"主题 {topic['topic_id']}: {', '.join(topic['keywords'][:8])}",
                        f"Topic {topic['topic_id']}: {', '.join(topic['keywords'][:8])}"
                    )
                )
        
        # 构建提示词 / Build prompt
        prompt = self._build_analysis_prompt(
            papers_summary='\n'.join(papers_summary),
            keywords=', '.join(top_keywords),
            topics='\n'.join(topic_descriptions),
            paper_count=len(papers)
        )
        
        # 获取配置的 max_tokens / Resolve max_tokens
        provider = self.config.get('llm', {}).get('provider', 'openai')
        provider_config = self.config.get('llm', {}).get(provider, {})
        # 默认增加到 8000，或者使用配置中的值 / Default to 8000 unless configured
        max_tokens = provider_config.get('max_tokens', 8000)
        
        try:
            self.logger.info(self.text(
                f"正在使用 LLM 生成分析报告 (max_tokens={max_tokens})...",
                f"Generating analysis with LLM (max_tokens={max_tokens})..."
            ))
            response = self.llm_client.generate(prompt, max_tokens=max_tokens)
            
            # 解析 LLM 响应 / Parse LLM response
            analysis = self._parse_llm_response(response)
            
            self.logger.info(self.text("✓ LLM 分析完成", "✓ LLM analysis completed"))
            
            return analysis
            
        except Exception as e:
            self.logger.error(self.text(f"LLM 分析失败: {str(e)}", f"LLM analysis failed: {str(e)}"))
            return {
                'analysis_summary': pick_text(self.config, f'生成失败: {str(e)}', f'Generation failed: {str(e)}'),
                'hotspots': pick_text(self.config, f'生成失败: {str(e)}', f'Generation failed: {str(e)}'),
                'trends': pick_text(self.config, f'生成失败: {str(e)}', f'Generation failed: {str(e)}'),
                'future_directions': pick_text(self.config, f'生成失败: {str(e)}', f'Generation failed: {str(e)}'),
                'research_ideas': pick_text(self.config, f'生成失败: {str(e)}', f'Generation failed: {str(e)}')
            }

    def _build_analysis_prompt(self, papers_summary: str, keywords: str, 
                              topics: str, paper_count: int) -> str:
        """构建 LLM 分析提示词
        
        Args:
            papers_summary: 论文摘要
            keywords: 关键词
            topics: 主题
            paper_count: 论文总数
            
        Returns:
            提示词字符串
        """
        if self.language == 'en':
            return f"""As a senior AI research expert, perform an in-depth analysis based on the latest {paper_count} arXiv papers below.

    ## Paper List (Top 30):
    {papers_summary}

    ## High-frequency Keywords:
    {keywords}

    ## Major Research Topics:
    {topics}

    Please provide a comprehensive analysis with this structure (answer in English):

    ### 1. Current Research Hotspots
    Identify the top 3-5 hottest research directions and explain why they are gaining attention.

    ### 2. Technical Trends
    Identify trends in technical development, including:
    - Dominant methods and architectures
    - Emerging new techniques
    - Evolution patterns observed from the papers

    ### 3. Future Directions
    Based on the current landscape, forecast likely directions in the next 6-12 months, including:
    - Possible extensions of current hotspots
    - Underexplored but promising opportunities
    - Potential breakthrough points

    ### 4. Research Ideas & Innovation Points
    Propose 5-8 innovative and feasible research ideas. For each idea include:
    - Core innovation
    - Why it is valuable
    - Possible technical implementation path
    - Potential application scenarios

    ### 5. Analysis Summary
    Provide one concise summary paragraph (3-6 sentences) that synthesizes the overall landscape.

    Please ensure the analysis is:
    - Grounded in actual paper content
    - Insightful and in-depth
    - Actionable for research planning
    - Forward-looking and innovation-focused

    Output in Markdown with clear headings and lists."""

        return f"""作为一位资深的 AI 研究专家，请基于以下 {paper_count} 篇最新的 arXiv 论文进行深入分析。

    ## 论文列表（前30篇）：
    {papers_summary}

    ## 高频关键词：
    {keywords}

    ## 主要研究主题：
    {topics}

    请按照以下结构进行全面分析（用中文回答）：

    ### 1. 当前研究热点分析 (Current Research Hotspots)
    分析当前这个研究领域最热门的3-5个研究方向，并说明为什么这些方向受到关注。

    ### 2. 技术趋势与演进 (Technical Trends)
    识别技术发展的趋势，包括：
    - 主流的技术方法和架构
    - 正在兴起的新技术
    - 从论文中观察到的技术演进路径

    ### 3. 未来发展方向 (Future Directions)
    基于当前研究状况，预测未来6-12个月可能的研究方向，包括：
    - 现有热点的可能延伸
    - 尚未充分探索但有潜力的方向
    - 可能的技术突破点

    ### 4. 创新研究想法 (Research Ideas & Innovation Points)
    提出5-8个具有创新性和可行性的研究想法，每个想法包括：
    - 核心创新点
    - 为什么这个想法有价值
    - 可能的技术实现路径
    - 潜在的应用场景

    ### 5. 分析总结 (Analysis Summary)
    用 1 段简洁总结（3-6 句）概括整体研究图景和关键判断。

    请确保分析：
    - 基于实际论文内容
    - 具有深度和洞察力
    - 提供可操作的研究方向
    - 突出创新性和前瞻性

    请用 Markdown 格式输出，使用清晰的标题和列表。"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应
        
        Args:
            response: LLM 响应文本
            
        Returns:
            解析后的分析结果
        """
        # 尝试按照标题分割 / Split by markdown headings
        sections = {
            'analysis_summary': '',
            'hotspots': '',
            'trends': '',
            'future_directions': '',
            'research_ideas': '',
            'full_analysis': response
        }
        
        # 简单的分割逻辑（可以根据实际响应格式调整）/ Simple splitting logic
        current_section = None
        current_content = []
        
        for line in response.split('\n'):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # 检查是否为标题行 (以 # 开头) / Heading line starts with '#'
            is_header = line_stripped.startswith('#')
            is_emphasis_header = line_stripped.startswith('**') and line_stripped.endswith('**')
            
            if (is_header or is_emphasis_header) and ('分析总结' in line or 'analysis summary' in line_lower or 'overall summary' in line_lower):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'analysis_summary'
                current_content = [line]
            elif is_header and ('研究热点' in line or 'hotspot' in line_lower):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'hotspots'
                current_content = [line]
            elif is_header and ('趋势' in line or 'trend' in line_lower):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'trends'
                current_content = [line]
            elif is_header and ('未来' in line or 'future' in line_lower or '发展方向' in line):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'future_directions'
                current_content = [line]
            elif is_header and ('创新' in line or 'idea' in line_lower or '想法' in line):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'research_ideas'
                current_content = [line]
            elif current_section:
                current_content.append(line)
        
        # 保存最后一个部分 / Save final section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        # Backward compatibility: if summary is not explicitly sectioned,
        # try extracting from trailing "分析总结" / "Analysis Summary" text.
        if not sections['analysis_summary']:
            summary_patterns = [
                r'(?:\*\*)?分析总结(?:\*\*)?\s*[:：]?\s*(.+)$',
                r'(?:\*\*)?analysis\s+summary(?:\*\*)?\s*[:：]?\s*(.+)$',
            ]
            for pattern in summary_patterns:
                m = re.search(pattern, response, flags=re.IGNORECASE | re.DOTALL)
                if m:
                    extracted = m.group(1).strip()
                    if extracted:
                        sections['analysis_summary'] = extracted
                        break
        
        return sections
    
    def _save_analysis(self, analysis: Dict[str, Any]):
        """保存分析结果
        
        Args:
            analysis: 分析结果
        """
        output_dir = Path('data/analysis')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = get_date_string()
        
        # 保存 JSON 格式 / Save JSON
        json_path = f"data/analysis/analysis_{date_str}.json"
        save_json(analysis, json_path)
        self.logger.info(self.text(f"💾 分析结果已保存: {json_path}", f"💾 Analysis saved: {json_path}"))
        
        # 保存最新分析（供 Web 服务使用）/ Save latest analysis for Web service
        latest_path = "data/analysis/latest.json"
        save_json(analysis, latest_path)
        self.logger.info(self.text(f"💾 最新分析已保存: {latest_path}", f"💾 Latest analysis saved: {latest_path}"))
        
        # 生成 Markdown 报告 / Generate markdown report
        markdown_path = f"data/analysis/report_{date_str}.md"
        self._generate_markdown_report(analysis, markdown_path)
        self.logger.info(self.text(f"📄 Markdown 报告已保存: {markdown_path}", f"📄 Markdown report saved: {markdown_path}"))
    
    def _generate_markdown_report(self, analysis: Dict[str, Any], output_path: str):
        """生成 Markdown 格式的分析报告
        
        Args:
            analysis: 分析结果
            output_path: 输出路径
        """
        llm_analysis = analysis.get('llm_analysis', {})
        statistics = analysis.get('statistics', {})
        keywords = analysis.get('keywords', [])
        
        if self.language == 'en':
            report = f"""# Research Trend Analysis Report

    **Date**: {analysis.get('date')}  
    **Analyzed Papers**: {analysis.get('paper_count')}  
    **Generated At**: {analysis.get('generated_at')}

    ---

    ## 📊 Statistical Overview

    - **Total Papers**: {statistics.get('total_papers', 0)}
    - **Total Authors**: {statistics.get('total_authors', 0)}
    - **Total Categories**: {statistics.get('total_categories', 0)}

    ### Category Distribution

    | Category | Paper Count |
    |----------|-------------|
    """
        else:
            report = f"""# 研究趋势分析报告

    **生成日期**: {analysis.get('date')}  
    **分析论文数**: {analysis.get('paper_count')}  
    **生成时间**: {analysis.get('generated_at')}

    ---

    ## 📊 统计概览

    - **总论文数**: {statistics.get('total_papers', 0)}
    - **涉及作者数**: {statistics.get('total_authors', 0)}
    - **研究类别数**: {statistics.get('total_categories', 0)}

    ### 类别分布

    | 类别 | 论文数 |
    |------|--------|
    """
        
        for cat, count in list(statistics.get('category_distribution', {}).items())[:10]:
            report += f"| {cat} | {count} |\n"
        
        report += "\n### High-frequency Keywords\n\n" if self.language == 'en' else "\n### 高频关键词\n\n"
        for kw in keywords[:20]:
            if self.language == 'en':
                report += f"- **{kw['keyword']}** (score: {kw['score']:.4f})\n"
            else:
                report += f"- **{kw['keyword']}** (权重: {kw['score']:.4f})\n"

        report += "\n---\n\n## 🔥 Current Research Hotspots\n\n" if self.language == 'en' else "\n---\n\n## 🔥 研究热点分析\n\n"
        report += llm_analysis.get('hotspots', 'Not generated' if self.language == 'en' else '未生成')
        
        report += "\n\n---\n\n## 📈 Technical Trends\n\n" if self.language == 'en' else "\n\n---\n\n## 📈 技术趋势与演进\n\n"
        report += llm_analysis.get('trends', 'Not generated' if self.language == 'en' else '未生成')
        
        report += "\n\n---\n\n## 🔮 Future Directions\n\n" if self.language == 'en' else "\n\n---\n\n## 🔮 未来发展方向\n\n"
        report += llm_analysis.get('future_directions', 'Not generated' if self.language == 'en' else '未生成')
        
        report += "\n\n---\n\n## 💡 Research Ideas\n\n" if self.language == 'en' else "\n\n---\n\n## 💡 创新研究想法\n\n"
        report += llm_analysis.get('research_ideas', 'Not generated' if self.language == 'en' else '未生成')

        report += "\n\n---\n\n## 🧭 Analysis Summary\n\n" if self.language == 'en' else "\n\n---\n\n## 🧭 分析总结\n\n"
        report += llm_analysis.get('analysis_summary', 'Not generated' if self.language == 'en' else '未生成')
        
        report += "\n\n---\n\n## 📸 Word Cloud\n\n" if self.language == 'en' else "\n\n---\n\n## 📸 词云图\n\n"
        report += f"![{'Word Cloud' if self.language == 'en' else '词云图'}]({analysis.get('wordcloud_path', '')})\n"
        
        report += "\n---\n\n*This report is generated automatically by Daily arXiv Agent*\n" if self.language == 'en' else "\n---\n\n*本报告由 Daily arXiv Agent 自动生成*\n"
        
        # 保存报告 / Write report file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def print_analysis_summary(self, analysis: Dict[str, Any]):
        """打印分析摘要
        
        Args:
            analysis: 分析结果
        """
        self.logger.info("\n" + "=" * 80)
        self.logger.info(self.text("📊 趋势分析摘要", "📊 Trend Analysis Summary"))
        self.logger.info("=" * 80)
        
        statistics = analysis.get('statistics', {})
        keywords = analysis.get('keywords', [])
        
        self.logger.info(self.text(f"\n总论文数: {statistics.get('total_papers', 0)}", f"\nTotal Papers: {statistics.get('total_papers', 0)}"))
        self.logger.info(self.text(f"涉及作者: {statistics.get('total_authors', 0)}", f"Authors Involved: {statistics.get('total_authors', 0)}"))
        self.logger.info(self.text(f"研究类别: {statistics.get('total_categories', 0)}", f"Research Categories: {statistics.get('total_categories', 0)}"))
        
        self.logger.info(self.text("\n高频关键词 (Top 15):", "\nHigh-frequency Keywords (Top 15):"))
        for kw in keywords[:15]:
            self.logger.info(f"  - {kw['keyword']}")
        
        self.logger.info(self.text("\n类别分布:", "\nCategory Distribution:"))
        for cat, count in list(statistics.get('category_distribution', {}).items())[:8]:
            self.logger.info(self.text(f"  - {cat}: {count} 篇", f"  - {cat}: {count} papers"))

        llm_analysis = analysis.get('llm_analysis', {})

        if llm_analysis.get('full_analysis'):
            self.logger.info("\n" + "=" * 80)
            self.logger.info(self.text("🤖 LLM 深度分析", "🤖 LLM In-depth Analysis"))
            self.logger.info("=" * 80)
            # 只打印前500个字符 / Print only first 500 chars
            full_text = llm_analysis.get('full_analysis', '')
            preview = full_text[:500] + "..." if len(full_text) > 500 else full_text
            self.logger.info(f"\n{preview}")
            self.logger.info(self.text(
                f"\n完整分析请查看: data/analysis/report_{analysis.get('date')}.md",
                f"\nSee full analysis: data/analysis/report_{analysis.get('date')}.md"
            ))
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info(self.text(f"📸 词云图: {analysis.get('wordcloud_path')}", f"📸 Word cloud: {analysis.get('wordcloud_path')}"))
        self.logger.info("=" * 80 + "\n")


def main():
    """测试函数 / Test helper"""
    from src.utils import load_config, load_env, setup_logging, load_json
    from src.summarizer.llm_factory import LLMClientFactory
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    text = lambda zh, en: pick_text(config, zh, en)
    
    # 加载论文数据 / Load paper data
    papers_data = load_json('data/papers/latest.json')
    if not papers_data:
        logger.error(text("未找到论文数据，请先运行论文爬取", "Paper data not found. Please run paper fetching first"))
        return
    
    papers = papers_data.get('papers', [])
    
    # 加载总结数据 / Load summary data
    summaries_data = load_json('data/summaries/latest.json')
    summaries = summaries_data.get('summaries', []) if summaries_data else None
    
    # 创建 LLM 客户端 / Create LLM client
    llm_client = LLMClientFactory.create_client(config)
    
    # 创建分析器 / Create analyzer
    analyzer = TrendAnalyzer(config, llm_client)
    
    # 执行分析 / Run analysis
    analysis = analyzer.analyze(papers, summaries)
    
    # 打印摘要 / Print summary
    analyzer.print_analysis_summary(analysis)


if __name__ == "__main__":
    main()
