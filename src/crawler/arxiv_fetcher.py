"""
arXiv 论文爬取器

使用 arxiv API 获取指定领域的最新论文
"""
import arxiv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from src.utils import save_json, get_date_string, get_data_path, get_language, pick_text


class ArxivFetcher:
    """arXiv 论文爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化 / Initialize
        
        Args:
            config: 配置字典 / Config dictionary
        """
        self.config = config
        self.language = get_language(config)
        self.text = lambda zh, en: pick_text(self.config, zh, en)
        self.arxiv_config = config.get('arxiv', {})
        self.logger = logging.getLogger('daily_arxiv.fetcher')
        
        # 获取配置 / Read configuration
        self.categories = self.arxiv_config.get('categories', ['cs.AI'])
        self.keywords = self.arxiv_config.get('keywords', [])
        self.max_results = self.arxiv_config.get('max_results', 20)
        self.sort_by = self.arxiv_config.get('sort_by', 'submittedDate')
        self.sort_order = self.arxiv_config.get('sort_order', 'descending')
        
    def build_query(self) -> str:
        """构建搜索查询 / Build search query
        
        Returns:
            查询字符串 / Query string
        """
        # 构建类别查询 / Build category query
        if len(self.categories) == 1:
            category_query = f"cat:{self.categories[0]}"
        else:
            category_parts = [f"cat:{cat}" for cat in self.categories]
            category_query = "(" + " OR ".join(category_parts) + ")"
        
        # 如果有关键词，添加关键词过滤 / Add keyword filter if provided
        if self.keywords:
            # 构建关键词查询（在标题或摘要中搜索）/ Search in title or abstract
            keyword_parts = []
            for keyword in self.keywords:
                # 在标题和摘要中搜索关键词 / Match keyword in title and abstract
                keyword_parts.append(f'(ti:"{keyword}" OR abs:"{keyword}")')
            keyword_query = "(" + " OR ".join(keyword_parts) + ")"
            
            # 组合类别和关键词 / Combine category and keyword query
            query = f"{category_query} AND {keyword_query}"
        else:
            query = category_query
        
        self.logger.info(self.text(f"构建的查询: {query}", f"Built query: {query}"))
        return query
    
    def fetch_papers(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """获取论文 / Fetch papers
        
        Args:
            days_back: 获取过去几天的论文，默认1天 / Number of days to look back
            
        Returns:
            论文列表 / Paper list
        """
        self.logger.info("=" * 60)
        self.logger.info(self.text("开始爬取 arXiv 论文", "Starting arXiv paper fetching"))
        self.logger.info(self.text(f"类别: {', '.join(self.categories)}", f"Categories: {', '.join(self.categories)}"))
        if self.keywords:
            self.logger.info(self.text(f"关键词: {', '.join(self.keywords)}", f"Keywords: {', '.join(self.keywords)}"))
        self.logger.info(self.text(f"最大结果数: {self.max_results}", f"Max results: {self.max_results}"))
        self.logger.info("=" * 60)
        
        # 构建查询 / Build query
        query = self.build_query()
        
        # 设置排序方式 / Resolve sorting options
        sort_by_map = {
            'submittedDate': arxiv.SortCriterion.SubmittedDate,
            'relevance': arxiv.SortCriterion.Relevance,
            'lastUpdatedDate': arxiv.SortCriterion.LastUpdatedDate,
        }
        sort_criterion = sort_by_map.get(self.sort_by, arxiv.SortCriterion.SubmittedDate)
        
        sort_order_map = {
            'descending': arxiv.SortOrder.Descending,
            'ascending': arxiv.SortOrder.Ascending,
        }
        sort_order = sort_order_map.get(self.sort_order, arxiv.SortOrder.Descending)
        
        # 创建搜索对象 / Create search object
        search = arxiv.Search(
            query=query,
            max_results=self.max_results,
            sort_by=sort_criterion,
            sort_order=sort_order
        )
        
        # 获取论文 / Fetch papers
        papers = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            self.logger.info(self.text("正在获取论文...", "Fetching papers..."))
            for result in search.results():
                # 检查提交日期 / Check published date
                if result.published.replace(tzinfo=None) < cutoff_date:
                    self.logger.debug(self.text(
                        f"论文 {result.title} 发布于 {result.published}，早于截止日期",
                        f"Paper '{result.title}' published at {result.published}, earlier than cutoff"
                    ))
                    continue
                
                # 提取论文信息 / Extract paper metadata
                paper = self._extract_paper_info(result)
                papers.append(paper)
                
                self.logger.info(f"✓ [{len(papers)}] {paper['title'][:60]}...")
            
            self.logger.info("=" * 60)
            self.logger.info(self.text(f"✅ 成功获取 {len(papers)} 篇论文", f"✅ Successfully fetched {len(papers)} papers"))
            self.logger.info("=" * 60)
            
            # 保存论文数据 / Save paper data
            self._save_papers(papers)
            
            return papers
            
        except Exception as e:
            self.logger.error(self.text(f"❌ 获取论文失败: {str(e)}", f"❌ Failed to fetch papers: {str(e)}"), exc_info=True)
            raise
    
    def _extract_paper_info(self, result: arxiv.Result) -> Dict[str, Any]:
        """提取论文信息 / Extract paper info
        
        Args:
            result: arxiv.Result 对象 / arxiv.Result object
            
        Returns:
            论文信息字典 / Paper info dict
        """
        return {
            'id': result.entry_id.split('/')[-1],  # arXiv ID
            'title': result.title,
            'authors': [author.name for author in result.authors],
            'abstract': result.summary.replace('\n', ' ').strip(),
            'categories': result.categories,
            'primary_category': result.primary_category,
            'published': result.published.isoformat(),
            'updated': result.updated.isoformat(),
            'pdf_url': result.pdf_url,
            'entry_url': result.entry_id,
            'comment': result.comment if hasattr(result, 'comment') else None,
            'journal_ref': result.journal_ref if hasattr(result, 'journal_ref') else None,
            'doi': result.doi if hasattr(result, 'doi') else None,
            'fetched_at': datetime.now().isoformat(),
        }
    
    def _save_papers(self, papers: List[Dict[str, Any]]):
        """保存论文数据 / Save papers
        
        Args:
            papers: 论文列表 / Paper list
        """
        if not papers:
            self.logger.warning(self.text("没有论文需要保存", "No papers to save"))
            return
        
        # 获取存储路径 / Resolve storage path
        data_path = get_data_path(self.config, 'papers')
        Path(data_path).mkdir(parents=True, exist_ok=True)
        
        # 按日期保存 / Save by date
        date_str = get_date_string()
        filepath = f"{data_path}/papers_{date_str}.json"
        
        # 保存数据 / Save data
        save_json(papers, filepath)
        self.logger.info(self.text(f"💾 论文数据已保存到: {filepath}", f"💾 Paper data saved to: {filepath}"))
        
        # 同时保存一份到 latest.json，方便 Web 服务读取 / Also save latest.json for Web app
        latest_filepath = f"{data_path}/latest.json"
        save_json({
            'date': date_str,
            'count': len(papers),
            'papers': papers
        }, latest_filepath)
        self.logger.info(self.text(f"💾 最新数据已保存到: {latest_filepath}", f"💾 Latest data saved to: {latest_filepath}"))
    
    def get_paper_stats(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取论文统计信息 / Get paper statistics
        
        Args:
            papers: 论文列表 / Paper list
            
        Returns:
            统计信息字典 / Statistics dict
        """
        if not papers:
            return {}
        
        # 统计类别分布 / Category distribution
        category_counts = {}
        for paper in papers:
            for category in paper['categories']:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # 统计作者数量 / Author counts
        author_counts = {}
        for paper in papers:
            for author in paper['authors']:
                author_counts[author] = author_counts.get(author, 0) + 1
        
        # 找出高产作者（发表2篇以上）/ Prolific authors (>=2 papers)
        prolific_authors = {k: v for k, v in author_counts.items() if v >= 2}
        
        stats = {
            'total_papers': len(papers),
            'category_distribution': category_counts,
            'total_authors': len(author_counts),
            'prolific_authors': prolific_authors,
            'date': get_date_string(),
        }
        
        return stats
    
    def print_paper_summary(self, papers: List[Dict[str, Any]]):
        """打印论文摘要 / Print paper summary
        
        Args:
            papers: 论文列表 / Paper list
        """
        if not papers:
            self.logger.info(self.text("没有找到论文", "No papers found"))
            return
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info(self.text(f"📚 今日论文摘要 ({len(papers)} 篇)", f"📚 Today's Paper Summary ({len(papers)} papers)"))
        self.logger.info("=" * 80)
        
        for i, paper in enumerate(papers, 1):
            self.logger.info(f"\n[{i}] {paper['title']}")
            self.logger.info(self.text(f"    作者: {', '.join(paper['authors'][:3])}", f"    Authors: {', '.join(paper['authors'][:3])}") + 
                           (" et al." if len(paper['authors']) > 3 else ""))
            self.logger.info(self.text(f"    类别: {', '.join(paper['categories'][:3])}", f"    Categories: {', '.join(paper['categories'][:3])}"))
            self.logger.info(self.text(f"    链接: {paper['pdf_url']}", f"    Link: {paper['pdf_url']}"))
            self.logger.info(self.text(f"    摘要: {paper['abstract'][:150]}...", f"    Abstract: {paper['abstract'][:150]}..."))
        
        # 显示统计信息 / Print statistics
        stats = self.get_paper_stats(papers)
        self.logger.info("\n" + "=" * 80)
        self.logger.info(self.text("📊 统计信息", "📊 Statistics"))
        self.logger.info("=" * 80)
        self.logger.info(self.text(f"总论文数: {stats['total_papers']}", f"Total papers: {stats['total_papers']}"))
        self.logger.info(self.text(f"总作者数: {stats['total_authors']}", f"Total authors: {stats['total_authors']}"))
        
        if stats.get('prolific_authors'):
            self.logger.info(self.text("\n高产作者 (2篇以上):", "\nProlific authors (2+ papers):"))
            for author, count in sorted(stats['prolific_authors'].items(), 
                                       key=lambda x: x[1], reverse=True)[:5]:
                self.logger.info(self.text(f"  - {author}: {count} 篇", f"  - {author}: {count} papers"))
        
        self.logger.info(self.text("\n类别分布:", "\nCategory distribution:"))
        for category, count in sorted(stats['category_distribution'].items(), 
                                     key=lambda x: x[1], reverse=True):
            self.logger.info(self.text(f"  - {category}: {count} 篇", f"  - {category}: {count} papers"))
        
        self.logger.info("=" * 80 + "\n")


def main():
    """测试函数"""
    from src.utils import load_config, load_env, setup_logging
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    
    fetcher = ArxivFetcher(config)
    papers = fetcher.fetch_papers(days_back=2)  # 获取过去2天的论文
    
    if papers:
        fetcher.print_paper_summary(papers)


if __name__ == "__main__":
    main()
