"""
阿里云 OSS 上传工具模块
"""
import os
import re
import logging
from typing import Optional, Dict, Any
from utils.file_utils import FileUtils

import oss2

logger = logging.getLogger(__name__)


class OSSUtils:
    """OSS 工具类"""

    def __init__(self, oss_config: Dict[str, str]):
        """
        初始化 OSS 工具

        Args:
            oss_config: OSS 配置字典，包含 access_key_id, access_key_secret, endpoint, bucket_name
        """
        self.oss_config = oss_config
        self.auth = oss2.Auth(
            self.oss_config['access_key_id'],
            self.oss_config['access_key_secret']
        )
        self.oss_bucket = oss2.Bucket(
            self.auth,
            self.oss_config['endpoint'],
            self.oss_config['bucket_name']
        )

    def upload_file(self, local_path: str, oss_path: str) -> Optional[str]:
        """
        上传文件到 OSS

        Args:
            local_path: 本地文件路径
            oss_path: OSS 存储路径

        Returns:
            OSS 访问 URL，失败则返回 None
        """
        if not os.path.exists(local_path):
            logger.error(f"本地文件不存在：{local_path}")
            return None

        try:
            logger.info(f"上传到 OSS: {local_path} -> {oss_path}")
            self.oss_bucket.put_object_from_file(oss_path, local_path)

            # 生成公共访问 URL
            url = f"https://{self.oss_config['bucket_name']}.{self.oss_config['endpoint']}/{oss_path}"
            logger.info(f"上传成功：{url}")
            return url

        except Exception as e:
            logger.error(f"上传到 OSS 失败：{str(e)}")
            return None

    def upload_file_with_cleanup(self, local_path: str, paper_title: str,
                                  output_dir: str) -> Optional[str]:
        """
        上传文件到 OSS（自动清理文件名）

        Args:
            local_path: 本地文件路径
            paper_title: 论文标题（用于生成 OSS 路径）
            output_dir: 输出目录

        Returns:
            OSS 访问 URL，失败则返回 None
        """
        if not self.oss_config:
            logger.info("OSS 配置未提供，跳过上传")
            return None

        if not os.path.exists(local_path):
            logger.error(f"错误：本地文件不存在 - {local_path}")
            return None

        try:
            # 清理文件名
            clean_title = FileUtils.clean_filename(paper_title)

            # 生成 OSS 路径
            oss_path = f"{output_dir}/{clean_title}/{os.path.basename(local_path)}"

            return self.upload_file(local_path, oss_path)

        except Exception as e:
            logger.error(f"上传到 OSS 失败：{str(e)}")
            return None

    def upload_images_batch(self, image_paths: Dict[str, str], paper_title: str,
                            output_dir: str) -> Dict[str, str]:
        """
        批量上传图片到 OSS

        Args:
            image_paths: 图片路径映射 {相对路径：完整本地路径}
            paper_title: 论文标题
            output_dir: 输出目录

        Returns:
            图片路径映射 {原始路径：OSS URL}
        """
        result_mapping = {}

        for rel_path, local_path in image_paths.items():
            oss_url = self.upload_file_with_cleanup(local_path, paper_title, output_dir)
            if oss_url:
                result_mapping[rel_path] = oss_url
                logger.info(f"图片上传成功：{rel_path} -> {oss_url}")
            else:
                logger.error(f"图片上传失败：{rel_path}")

        return result_mapping
