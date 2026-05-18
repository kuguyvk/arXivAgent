"""
PDF 处理模块
负责 PDF 下载和 MinerU 分析
"""
import os
import logging
from typing import Tuple, Optional, Any

import requests
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

from utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF 处理器类"""

    def __init__(self, pdf_dir: str, markdown_dir: str, image_base_dir: str):
        """
        初始化 PDF 处理器

        Args:
            pdf_dir: PDF 存储目录
            markdown_dir: Markdown 输出目录
            image_base_dir: 图片存储基础目录
        """
        self.pdf_dir = pdf_dir
        self.markdown_dir = markdown_dir
        self.image_base_dir = image_base_dir

    def download_paper(
        self,
        paper: Any,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Optional[str]:
        """
        下载论文 PDF

        Args:
            paper: arXiv 论文对象
            max_retries: 最大重试次数
            retry_delay: 重试延迟

        Returns:
            下载的 PDF 文件路径，失败则返回 None
        """
        # 清理文件名
        clean_title = FileUtils.clean_filename(paper.title)
        file_path = os.path.join(self.pdf_dir, f"{clean_title}.pdf")

        # 检查文件是否已存在
        if FileUtils.file_exists(file_path):
            logger.info(f"文件已存在：{file_path}")
            return file_path

        try:
            logger.info(f"下载论文：{paper.title}")
            response = requests.get(paper.pdf_url, timeout=30)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"已保存到：{file_path}")
            return file_path

        except Exception as e:
            logger.error(f"下载论文失败：{str(e)}")
            return None

    def minerU_analysis(self, pdf_path: str) -> Tuple[str, str]:
        """
        使用 MinerU 分析 PDF 文件

        Args:
            pdf_path: PDF 文件路径

        Returns:
            (Markdown 文件路径，JSON 文件路径)
        """
        try:
            # 提取文件名（不含后缀）
            name_without_suffix = FileUtils.extract_name_without_suffix(pdf_path)

            # 设置输出目录
            local_image_dir = os.path.join(self.image_base_dir, name_without_suffix)
            local_md_dir = self.markdown_dir
            image_dir = os.path.basename(local_image_dir)

            # 确保图片目录存在
            FileUtils.ensure_directory(local_image_dir)

            # 初始化读写对象
            image_writer = FileBasedDataWriter(local_image_dir)
            md_writer = FileBasedDataWriter(local_md_dir)
            pdf_bytes = FileBasedDataReader("").read(pdf_path)

            # 加载数据集并推理
            ds = PymuDocDataset(pdf_bytes)

            # 根据 PDF 类型选择处理方式
            if ds.classify() == SupportedPdfParseMethod.OCR:
                logger.info(f"使用 OCR 模式处理：{name_without_suffix}")
                infer_result = ds.apply(doc_analyze, ocr=True)
                pipe_result = infer_result.pipe_ocr_mode(image_writer)
            else:
                logger.info(f"使用文本模式处理：{name_without_suffix}")
                infer_result = ds.apply(doc_analyze, ocr=False)
                pipe_result = infer_result.pipe_txt_mode(image_writer)

            # 输出 Markdown 和 JSON
            pipe_result.dump_md(md_writer, f"{name_without_suffix}.md", image_dir)
            pipe_result.dump_content_list(md_writer, f"{name_without_suffix}.json", image_dir)

            md_path = os.path.join(self.markdown_dir, f"{name_without_suffix}.md")
            json_path = os.path.join(self.markdown_dir, f"{name_without_suffix}.json")

            logger.info(f"MinerU 分析完成：MD={md_path}, JSON={json_path}")
            return md_path, json_path

        except Exception as e:
            logger.error(f"MinerU 分析失败：{str(e)}")
            raise
