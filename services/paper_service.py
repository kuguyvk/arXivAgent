"""
论文服务模块
整合核心模块，提供完整的论文处理服务
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional, Generator

from config import Config
from utils.file_utils import FileUtils
from utils.text_utils import TextUtils
from core.paper_searcher import PaperSearcher
from core.pdf_processor import PDFProcessor
from core.summarizer import Summarizer

logger = logging.getLogger(__name__)


class PaperService:
    """论文处理服务类"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        output_dir: str = "papers",
        oss_config: Optional[Dict[str, str]] = None
    ):
        """
        初始化论文服务

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model_name: 模型名称
            output_dir: 输出目录
            oss_config: OSS 配置
        """
        self.api_key = api_key
        self.output_dir = output_dir
        self.oss_config = oss_config

        # 创建目录结构
        self._init_directories()

        # 初始化核心组件
        self.searcher = PaperSearcher()
        self.pdf_processor = PDFProcessor(
            pdf_dir=self.pdf_dir,
            markdown_dir=self.md_dir,
            image_base_dir=self.image_dir
        )
        self.summarizer = Summarizer(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            image_dir=self.image_dir,
            markdown_dir=self.md_dir,
            oss_config=oss_config,
            output_dir=output_dir
        )

    def _init_directories(self) -> None:
        """初始化目录结构"""
        dirs = FileUtils.create_output_structure(
            self.output_dir,
            [Config.PDF_SUBDIR, Config.MARKDOWN_SUBDIR, Config.IMAGE_SUBDIR, Config.SUMMARY_SUBDIR]
        )
        self.pdf_dir = dirs[Config.PDF_SUBDIR]
        self.md_dir = dirs[Config.MARKDOWN_SUBDIR]
        self.image_dir = dirs[Config.IMAGE_SUBDIR]
        self.summary_dir = dirs[Config.SUMMARY_SUBDIR]

        logger.info(f"初始化目录结构完成：{self.output_dir}")

    def search_papers(
        self,
        query: str,
        max_results: int = 5,
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> List[Any]:
        """
        搜索论文

        Args:
            query: 搜索查询
            max_results: 最大结果数
            sort_by: 排序字段
            sort_order: 排序顺序

        Returns:
            论文列表
        """
        return self.searcher.search_papers(query, max_results, sort_by, sort_order)

    def process_paper(self, paper: Any) -> Dict[str, Any]:
        """
        处理单篇论文

        Args:
            paper: arXiv 论文对象

        Returns:
            处理结果字典
        """
        # 处理作者列表
        author_names = TextUtils.extract_authors(paper.authors)

        try:
            # 下载 PDF
            pdf_path = self.pdf_processor.download_paper(paper)
            if not pdf_path:
                raise Exception("PDF 下载失败")

            # MinerU 分析
            md_path, json_path = self.pdf_processor.minerU_analysis(pdf_path)

            # 生成摘要
            logger.info(f"生成摘要：{paper.title}")
            summary = self.summarizer.generate_summary(paper, md_path, json_path)

            # 保存摘要
            result = self.save_summary(paper, summary)

            return {
                "title": paper.title,
                "authors": author_names.split(', '),
                "published": str(paper.published),
                "markdown_content": result,
                "success": True
            }

        except Exception as e:
            logger.error(f"处理论文失败：{str(e)}")
            return {
                "title": paper.title,
                "authors": author_names.split(', ') if author_names else [],
                "success": False,
                "error": str(e)
            }

    def process_papers(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量处理论文

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            处理结果列表
        """
        logger.info(f"搜索论文，查询：{query}")
        papers = self.search_papers(query, max_results)
        logger.info(f"找到 {len(papers)} 篇论文")

        results = []

        for i, paper in enumerate(papers):
            logger.info(f"\n处理论文 {i + 1}/{len(papers)}: {paper.title}")

            result = self.process_paper(paper)
            results.append(result)

            # 添加延迟以避免 API 限制
            if i < len(papers) - 1:
                time.sleep(Config.API_RETRY_DELAY)

        return results

    def process_papers_stream(
        self,
        query: str,
        max_results: int = 5
    ) -> Generator[str, None, None]:
        """
        流式处理论文（用于 API 响应）

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Yields:
            JSON 格式的流式响应
        """
        import json

        try:
            papers = self.search_papers(query, max_results)
            total = len(papers)

            # 发送初始状态
            yield json.dumps({
                "type": "status",
                "message": f"找到 {total} 篇论文，开始处理...",
                "total": total,
                "processed": 0
            }) + "\n"

            for i, paper in enumerate(papers):
                # 发送开始处理通知
                yield json.dumps({
                    "type": "status",
                    "message": f"正在处理论文 {i + 1}/{total}: {paper.title[:50]}...",
                    "total": total,
                    "processed": i,
                    "current": i + 1
                }) + "\n"

                result = self.process_paper(paper)

                # 发送处理结果
                yield json.dumps({
                    "type": "paper",
                    "data": result,
                    "processed": i + 1,
                    "total": total
                }) + "\n"

                # 添加延迟
                if i < len(papers) - 1:
                    time.sleep(Config.API_RETRY_DELAY)

            # 发送完成通知
            yield json.dumps({
                "type": "complete",
                "message": "所有论文处理完成",
                "processed": total,
                "total": total
            }) + "\n"

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": f"处理过程中出错：{str(e)}"
            }) + "\n"

    def save_summary(self, paper: Any, summary: str) -> str:
        """
        保存论文摘要

        Args:
            paper: arXiv 论文对象
            summary: 摘要内容

        Returns:
            完整内容（包含元数据）
        """
        # 清理文件名
        clean_title = FileUtils.clean_filename(paper.title)
        file_path = os.path.join(self.summary_dir, f"{clean_title}_summary.md")

        # 处理作者列表
        authors_str = TextUtils.extract_authors(paper.authors)

        # 创建元数据头部
        metadata = f"""# {paper.title}

- **作者**: {authors_str}
- **发布日期**: {paper.published}
- **arXiv ID**: {paper.entry_id}
- **链接**: {paper.pdf_url}
- **类别**: {', '.join(paper.categories)}

## 摘要

{paper.summary}

## AI 生成的分析

"""

        # 写入文件
        FileUtils.write_text_file(file_path, metadata + summary)

        logger.info(f"摘要已保存到：{file_path}")
        return metadata + summary
