"""
论文搜索模块
"""
import logging
from typing import List, Any, Dict, Optional

import arxiv

logger = logging.getLogger(__name__)


class PaperSearcher:
    """论文搜索类"""

    def __init__(self):
        """初始化论文搜索器"""
        pass

    def search_papers(
        self,
        query: str,
        max_results: int = 5,
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> List[Any]:
        """
        搜索 arXiv 论文

        Args:
            query: 搜索查询
            max_results: 最大结果数
            sort_by: 排序字段 (submittedDate, relevance)
            sort_order: 排序顺序 (descending, ascending)

        Returns:
            论文结果列表
        """
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate if sort_by == "submittedDate"
                else arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending if sort_order == "descending"
                else arxiv.SortOrder.Ascending
            )

            results = list(search.results())
            logger.info(f"搜索到 {len(results)} 篇论文")
            return results

        except Exception as e:
            logger.error(f"搜索论文失败：{str(e)}")
            return []

    def build_query(
        self,
        category: str,
        keyword: str,
        date_from: str,
        date_to: str
    ) -> str:
        """
        构建 arXiv 搜索查询

        Args:
            category: 论文类别（如 cs.CV）
            keyword: 关键词
            date_from: 起始日期（如 20250518）
            date_to: 结束日期（如 20250520）

        Returns:
            构建好的查询字符串
        """
        return f"cat:{category} AND all:{keyword} AND submittedDate:[{date_from} TO {date_to}]"
