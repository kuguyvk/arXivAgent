"""
摘要生成模块
负责调用大模型 API 生成论文摘要
"""
import os
import logging
from typing import Dict, Any, Optional

from openai import OpenAI

from google import genai
from google.genai import types
import pathlib

from config import Config, PromptTemplates
from utils.file_utils import FileUtils
from utils.oss_utils import OSSUtils
from utils.text_utils import TextUtils

logger = logging.getLogger(__name__)


class Summarizer:
    """论文摘要生成器"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        image_dir: str,
        markdown_dir: str,
        oss_config: Optional[Dict[str, str]] = None,
        output_dir: str = "papers"
    ):
        """
        初始化摘要生成器

        Args:
            api_key: API 密钥
            image_dir: 图片目录
            markdown_dir: Markdown 目录
            oss_config: OSS 配置
            output_dir: 输出目录
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.image_dir = image_dir
        self.markdown_dir = markdown_dir
        self.output_dir = output_dir

        # 初始化 OpenAI 客户端（使用兼容 API）
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

        # 初始化 OSS 工具
        self.oss_utils = OSSUtils(oss_config) if oss_config else None

    def _prepare_image_prompt(self, image_dir: str, paper_title: str) -> str:
        """
        准备图片提示词

        Args:
            image_dir: 图片目录
            paper_title: 论文标题

        Returns:
            图片提示词字符串
        """
        image_list = FileUtils.get_image_files(image_dir)
        all_image_mapping = {}

        for local_img_filename in image_list:
            local_img_path = os.path.join(image_dir, local_img_filename)

            # 上传到 OSS
            oss_url = self.oss_utils.upload_file_with_cleanup(
                local_img_path, paper_title, self.output_dir
            )

            if oss_url:
                all_image_mapping[local_img_path] = oss_url
                logger.info(f"图片上传成功：{local_img_path} -> {oss_url}")
            else:
                logger.warning(f"图片上传失败：{local_img_path}")

        if all_image_mapping:
            # 使用相对路径格式让大模型引用图片，后续再由代码替换为 OSS URL
            # 这样大模型生成的 summary 中使用的是相对路径，便于后续替换
            image_paths_text = "\n".join(f"![]({path})" for path in all_image_mapping.keys())
            return f"\n以下是论文中的所有图表，请在分析中引用它们（使用以下相对路径引用图片）：\n{image_paths_text}"
        return ""

    def _call_llm_api(self, prompt: str, md_path: str, json_path: str,image_paths) -> str:
        """
        调用大模型 API

        Args:
            prompt: 提示词
            md_content: Markdown 路径
            json_content: JSON 路径

        Returns:
            生成的摘要
        """
        try:

            mdpath = pathlib.Path(md_path)
            jsonpath = pathlib.Path(json_path)


            # response = self.client.models.generate_content(
            #     model="gemini-2.5-flash",
            #     contents=[
            #         prompt,
            #         types.Part.from_bytes(
            #             data=mdpath.read_bytes(),
            #             mime_type='text/plain',
            #         ),
            #         types.Part.from_bytes(
            #             data=jsonpath.read_bytes(),
            #             mime_type='text/javascript',
            #         ),
            #         image_list,
            #     ]
            # )

            # summary = response.text



            md_content = FileUtils.read_file_text(md_path)
            json_content = FileUtils.read_file_text(json_path)

            # img_content = []
            # for img_path in image_paths:
            #     base64_img=FileUtils.encode_image(img_path)
            #     img_content.append({
            #         "type":"image_url",
            #         "image_url":{
            #             "url":f"data:image/png;base64,{base64_img}"
            #         },
            #     })



            messages = [
                {"role": "user", "content": prompt},
                {"role": "user", "content": md_content},
                {"role": "user", "content": json_content},
            ]



            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            
            print("API 响应：", response)
            
            if isinstance(response, str):
                summary = response

            elif hasattr(response, "choices") and response.choices:
                summary = response.choices[0].message.content

            elif isinstance(response, dict):
                summary = response.get("choices", [{}])[0].get("message", {}).get("content")

            else:
                raise ValueError(f"未知响应格式: {response}")


            return summary

        except Exception as e:
            logger.error(f"调用 API 生成摘要时出错：{str(e)}")
            return f"生成摘要失败：{str(e)}"

    def _replace_image_paths(
        self,
        summary: str,
        image_dir: str,
        paper_title: str
    ) -> str:
        """
        替换摘要中的图片路径为 OSS URL

        Args:
            summary: 原始摘要
            image_dir: 图片目录
            paper_title: 论文标题

        Returns:
            替换后的摘要
        """
        img_paths = TextUtils.extract_markdown_images(summary)
        logger.info(f"提取到的图片路径：{img_paths}")

        # 上传图片并替换路径
        for img_path in img_paths:
            local_img_path = os.path.join(image_dir, img_path)
            oss_url = self.oss_utils.upload_file_with_cleanup(
                local_img_path, paper_title, self.output_dir
            )

            if oss_url:
                logger.info(f"图片上传成功：{img_path} -> {oss_url}")
                summary = summary.replace(img_path, oss_url)
                logger.info(f"图片路径替换：{img_path} -> {oss_url}")
            else:
                logger.error(f"图片上传失败：{img_path}")

        return summary

    def generate_summary(
        self,
        paper: Any,
        md_path: str,
        json_path: str
    ) -> str:
        """
        生成论文摘要

        Args:
            paper: arXiv 论文对象
            md_path: Markdown 文件路径
            json_path: JSON 文件路径

        Returns:
            生成的摘要
        """
        try:
            # 处理作者列表
            authors_str = TextUtils.extract_authors(paper.authors)

            # 准备提示词
            prompt = PromptTemplates.get_analysis_prompt(
                paper.title,
                authors_str,
                str(paper.published)
            )


            # 清理标题用于目录构建
            clean_title = FileUtils.clean_filename(paper.title)
            image_dir = os.path.join(self.image_dir, clean_title)

            image_paths = []
            for f in os.listdir(image_dir):
                image_paths.append(os.path.join(image_dir, f))

            #image_prompt = self._prepare_image_prompt(image_dir, paper.title)
            #prompt += image_prompt

            # 调用 LLM API
            summary = self._call_llm_api(prompt, md_path, json_path,image_paths)

            # 替换图片路径（大模型使用的是相对路径，需要替换为 OSS URL）
            summary = self._replace_image_paths(summary, self.image_dir, paper.title)

            return summary

        except Exception as e:
            logger.error(f"生成摘要失败：{str(e)}")
            return f"生成摘要失败：{str(e)}"
