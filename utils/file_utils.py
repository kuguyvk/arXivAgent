"""
文件处理工具模块
"""
import os
import re
import pathlib
from typing import Tuple, List, Dict, Any
import base64


class FileUtils:
    """文件处理工具类"""

    @staticmethod
    def auto_output_dir(category, keyword, date_from=None, date_to=None):
        """自动生成输出目录名"""

        return f"{date_from}-{date_to}_{category.replace('.', '')}_{keyword.replace(' ', '_').replace(',', '-')}"

    @staticmethod
    def clean_filename(title: str, max_length: int = 100) -> str:
        """
        清理文件名，移除特殊字符

        Args:
            title: 原始标题
            max_length: 最大长度限制

        Returns:
            清理后的文件名
        """
        # 去掉特殊字符，保留字母、数字、下划线、连字符、点和空格
        clean_title = re.sub(r'[^\w\-_. ]', '_', title)
        # 将空格替换为下划线
        clean_title = clean_title.replace(" ", "_")
        # 限制长度
        return clean_title[:max_length]

    @staticmethod
    def extract_name_without_suffix(filepath: str) -> str:
        """
        从文件路径提取不含后缀的文件名

        Args:
            filepath: 文件路径

        Returns:
            不含后缀的文件名
        """
        return os.path.splitext(os.path.basename(filepath))[0]

    @staticmethod
    def ensure_directory(dir_path: str) -> None:
        """
        确保目录存在，不存在则创建

        Args:
            dir_path: 目录路径
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    @staticmethod
    def create_output_structure(base_dir: str, subdirs: List[str]) -> Dict[str, str]:
        """
        创建输出目录结构

        Args:
            base_dir: 基础目录
            subdirs: 子目录列表

        Returns:
            包含各目录路径的字典
        """
        # 创建基础目录
        FileUtils.ensure_directory(base_dir)

        # 创建子目录
        dir_paths = {}
        for subdir in subdirs:
            full_path = os.path.join(base_dir, subdir)
            FileUtils.ensure_directory(full_path)
            dir_paths[subdir] = full_path

        return dir_paths

    @staticmethod
    def read_file_bytes(filepath: str) -> bytes:
        """
        读取文件字节内容

        Args:
            filepath: 文件路径

        Returns:
            文件字节内容
        """
        return pathlib.Path(filepath).read_bytes()

    @staticmethod
    def read_file_text(filepath: str, encoding: str = "utf-8") -> str:
        """
        读取文件文本内容

        Args:
            filepath: 文件路径
            encoding: 编码格式

        Returns:
            文件文本内容
        """
        return pathlib.Path(filepath).read_text(encoding=encoding)

    @staticmethod
    def get_image_files(image_dir: str) -> List[str]:
        """
        获取目录下的所有图片文件

        Args:
            image_dir: 图片目录

        Returns:
            图片文件名列表
        """
        if not os.path.exists(image_dir):
            return []
        return os.listdir(image_dir)
    
    @staticmethod
    def encode_image(image_path: str) -> str:
        """
        将图片编码为 Base64 字符串

        Args:
            image_path: 图片文件路径

        Returns:
            Base64 编码字符串
        """
        import base64
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    @staticmethod
    def write_text_file(filepath: str, content: str, encoding: str = "utf-8") -> None:
        """
        写入文本文件

        Args:
            filepath: 文件路径
            content: 文件内容
            encoding: 编码格式
        """
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """
        检查文件是否存在

        Args:
            filepath: 文件路径

        Returns:
            是否存在
        """
        return os.path.exists(filepath)
