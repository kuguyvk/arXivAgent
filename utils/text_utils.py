"""
文本处理工具模块
"""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TextUtils:
    """文本处理工具类"""

    @staticmethod
    def extract_markdown_images(summary: str) -> List[str]:
        """
        从 Markdown 内容中提取图片路径

        Args:
            summary: Markdown 文本

        Returns:
            图片路径列表
        """
        img_paths = []

        # 匹配标准的 Markdown 图片语法
        img_pattern = re.compile(r'!\[\]\((.*?)\)')

        # 查找所有匹配的图片路径
        matches = img_pattern.findall(summary)
        logger.info(f"在 markdown 文档中找到的图片路径：{matches}")

        # 过滤出有效的图片路径
        for path in matches:
            path = path.strip()
            if path:
                img_paths.append(path)
                logger.info(f"提取到有效图片路径：{path}")
            else:
                logger.info(f"忽略非本地图片路径：{path}")

        return img_paths

    @staticmethod
    def extract_authors(authors_list: List[Any]) -> str:
        """
        从作者列表提取作者名字符串

        Args:
            authors_list: 作者对象列表

        Returns:
            逗号分隔的作者名字符串
        """
        author_names = []
        for author in authors_list:
            if hasattr(author, 'name'):
                author_names.append(author.name)
            else:
                author_names.append(str(author))

        return ', '.join(author_names)

    @staticmethod
    def clean_markdown_to_text(markdown_content: str) -> str:
        """
        清除 Markdown 格式，转换为纯文本

        Args:
            markdown_content: Markdown 内容

        Returns:
            纯文本内容
        """
        start_marker = "1.  **论文的主要贡献和创新点:**"
        start_index = markdown_content.find(start_marker)

        if start_index == -1:
            logger.info("未找到分析部分的起始标记，未生成 txt 内容")
            return ""

        # 截取从 start_marker 开始的内容
        text = markdown_content[start_index:].strip()

        # 清除 Markdown 格式
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **加粗**
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # *斜体*
        text = re.sub(r'\[(.*?)\]\([^)]+\)', r'\1', text)  # [链接文本](url)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # ```代码块```
        text = re.sub(r'`([^`]+)`', r'\1', text)  # `行内代码`
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # - 列表
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # 1. 有序列表
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)  # > 引用
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)  # --- 分割线
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 多余空行

        return text.strip()

    @staticmethod
    def replace_image_paths(text: str, path_mapping: Dict[str, str]) -> str:
        """
        替换文本中的图片路径为 OSS URL

        Args:
            text: 原始文本
            path_mapping: 路径映射 {原路径：OSS URL}

        Returns:
            替换后的文本
        """
        result = text
        for old_path, new_url in path_mapping.items():
            result = result.replace(old_path, new_url)
        return result
