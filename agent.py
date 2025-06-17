import argparse
import os
import time
import arxiv
from google import genai
from google.genai import types
import pathlib
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
import requests

from utils import (
    ImageUtils,
    OSSUploader,
    FileUtils,
    StringUtils,
    load_oss_config
)


class ArxivPaperSummarizer:
    def __init__(self, api_key, api_base="https://api-inference.modelscope.cn/v1/", output_dir="papers"):
        self.api_base = api_base
        self.output_dir = output_dir
        self.client = genai.Client(api_key=api_key)

        # OSS配置
        self.oss_config = load_oss_config()

        # 初始化OSS上传器
        self.oss_uploader = OSSUploader(self.oss_config)

        # 创建目录结构
        subdirs = ["pdfs", "markdowns", "images", "summaries"]
        dir_paths = FileUtils.create_directory_structure(output_dir, subdirs)

        self.pdf_dir = dir_paths["pdfs"]
        self.md_dir = dir_paths["markdowns"]
        self.image_dir = dir_paths["images"]
        self.summary_dir = dir_paths["summaries"]

    def search_papers(self, query, max_results=5, sort_by="submittedDate", sort_order="descending"):
        """搜索arXiv论文"""
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate if sort_by == "submittedDate" else arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending if sort_order == "descending" else arxiv.SortOrder.Ascending
        )
        return list(search.results())

    def download_paper(self, paper):
        """下载论文PDF"""
        # 使用工具函数清理文件名
        clean_title = FileUtils.clean_filename(paper.title)
        file_path = os.path.join(self.pdf_dir, f"{clean_title}.pdf")

        # 检查文件是否已存在
        if os.path.exists(file_path):
            print(f"文件已存在: {file_path}")
            return file_path

        response = requests.get(paper.pdf_url, timeout=30)
        response.raise_for_status()

        print(f"下载论文: {paper.title}")
        with open(file_path, 'wb') as f:
            f.write(response.content)

        print(f"已保存到: {file_path}")
        return file_path

    def minerU_analysis(self, pdfpath):
        """使用MinerU分析PDF并转换为Markdown"""
        pdf_file_name = pdfpath
        name_without_suff = os.path.splitext(os.path.basename(pdf_file_name))[0]

        local_image_dir = f"{self.image_dir}/{name_without_suff}"
        local_md_dir = self.md_dir
        image_dir = os.path.basename(local_image_dir)

        os.makedirs(local_image_dir, exist_ok=True)

        # 初始化读写对象
        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(local_md_dir)
        pdf_bytes = FileBasedDataReader("").read(pdf_file_name)

        # 加载数据集并推理
        ds = PymuDocDataset(pdf_bytes)

        if ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)

        pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
        pipe_result.dump_content_list(md_writer, f"{name_without_suff}.json", image_dir)

        mdpath = os.path.join(self.md_dir, f"{name_without_suff}.md")
        jsonpath = os.path.join(self.md_dir, f"{name_without_suff}.json")

        return mdpath, jsonpath

    def generate_summary(self, paper, mdpath, jsonpath):
        """生成论文摘要"""
        # 使用工具函数格式化作者
        authors_str = StringUtils.format_authors(paper.authors)

        # 准备提示词
        prompt = f"""我给你的是一篇学术论文的markdown文档以及相应的json文件，还有从论文中提取出的图表，请你帮我做以下分析：
1. 用中文总结论文的主要贡献和创新点（200字以内）
2. 列出论文使用的主要方法和技术
3. 分析这篇论文的实验结果
4. 如果论文中有图表，请从该论文中选出最具有价值的一张图和一张表，分别进行简要分析。

**重要说明：** 在插入图片时，请严格按照以下要求：
- 从json文件中找到对应图表的img_path字段
- **直接使用img_path的值，不要添加任何前缀、后缀或修改路径**
- img_path示例格式：General-purpose_audio_representation_learning_for_real-world_sound_scenes/a8c56e770318044471c290ecde37f586a95fcc8649715aeeddcaf034243f6e4b.jpg
- **禁止在路径前添加任何目录前缀（如images/、../images/等）**

请严格按照下面格式输出，包括缩进、标点、符号和换行：
    *   **最有价值的图:**
        *   图编号+标题
        *   ![](【直接使用json中的img_path值】)
        *   **分析:** 

    *   **最有价值的表:**
        *   表编号+标题
        *   ![](【直接使用json中的img_path值】)
        *   **分析:** 

5. 总结这篇论文

论文标题: {paper.title}
论文作者: {authors_str}
发表日期: {paper.published}     
        """

        try:
            # 调用大模型 API
            filepath = pathlib.Path(mdpath)
            filepath2 = pathlib.Path(jsonpath)

            clean_title = FileUtils.clean_filename(paper.title)
            image_dir = f"{self.image_dir}/{clean_title}"

            image_list = []
            for f in os.listdir(image_dir) if os.path.exists(image_dir) else []:
                image_path = os.path.join(image_dir, f)
                if os.path.isfile(image_path):
                    image_list.append(image_path)

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=filepath.read_bytes(),
                        mime_type='text/md',
                    ),
                    types.Part.from_bytes(
                        data=filepath2.read_bytes(),
                        mime_type='text/javascript',
                    ),
                    *image_list,  # 展开图片列表
                ]
            )

            summary = response.text

            # 使用工具类处理图片路径
            img_paths = ImageUtils.extract_image_paths(summary)
            print(f"提取到的图片路径: {img_paths}")

            # 上传图片到OSS
            for img_path in img_paths:
                # 构建本地完整路径
                local_img_path = os.path.join(self.image_dir, img_path)

                # 使用OSS上传器上传
                oss_url = self.oss_uploader.upload_to_oss(local_img_path, paper.title,self.output_dir)

                if oss_url:
                    summary = summary.replace(img_path, oss_url)
                else:
                    print(f"图片上传失败: {img_path}")

            return summary

        except Exception as e:
            print(f"调用API生成摘要时出错: {str(e)}")
            return f"生成摘要失败: {str(e)}"

    def save_summary(self, paper, summary):
        """保存摘要到文件"""
        # 使用工具函数清理文件名
        clean_title = FileUtils.clean_filename(paper.title)
        file_path = os.path.join(self.summary_dir, f"{clean_title}_summary.md")

        # 使用工具函数格式化作者
        authors_str = StringUtils.format_authors(paper.authors)

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
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(metadata + summary)

        print(f"摘要已保存到: {file_path}")
        return metadata + summary

    def process_papers(self, query, max_results=5):
        """处理论文的主要流程"""
        # 搜索论文
        print(f"搜索论文，查询: {query}")
        papers = self.search_papers(query, max_results=max_results)
        print(f"找到 {len(papers)} 篇论文")

        results = []

        # 处理每篇论文
        for i, paper in enumerate(papers):
            print(f"\n处理论文 {i + 1}/{len(papers)}: {paper.title}")

            # 使用工具函数格式化作者
            author_names = StringUtils.format_authors(paper.authors).split(', ')

            try:
                # 下载PDF
                pdf_path = self.download_paper(paper)

                # 转换markdown提取图表
                markdown_path, json_path = self.minerU_analysis(pdf_path)

                # 生成摘要
                print("生成摘要...")
                summary = self.generate_summary(paper, markdown_path, json_path)

                # 保存摘要
                result = self.save_summary(paper, summary)

                results.append({
                    "title": paper.title,
                    "authors": author_names,
                    "published": str(paper.published),
                    "markdown_content": result,
                    "success": True
                })

            except Exception as e:
                print(f"处理论文时出错: {str(e)}")
                results.append({
                    "title": paper.title,
                    "authors": author_names,
                    "success": False
                })

            time.sleep(2)

        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='arXiv论文摘要生成工具')
    parser.add_argument('--api_key', type=str, required=True, help="Gemini api-key")
    parser.add_argument('--api_base', type=str, default='https://api-inference.modelscope.cn/v1/')
    parser.add_argument('--max_results', type=int, required=True)
    parser.add_argument('--category', type=str, required=True, help="领域，如 cs.CV")
    parser.add_argument('--keyword', type=str, required=True, help="关键词，如 emotion")
    parser.add_argument('--date_from', type=str, required=True, help="起始日期，如 20250518")
    parser.add_argument('--date_to', type=str, required=True, help="结束日期，如 20250520")

    args = parser.parse_args()

    query = f"cat:{args.category} AND all:{args.keyword} AND submittedDate:[{args.date_from} TO {args.date_to}]"
    output_dir =f"{args.date_from}-{args.date_to}_{args.category.replace('.', '')}_{args.keyword}"


    # 初始化摘要生成器
    summarizer = ArxivPaperSummarizer(
        api_key=args.api_key,
        api_base=args.api_base,
        output_dir=output_dir
    )

    # 处理论文
    results = summarizer.process_papers(
        query=query,
        max_results=args.max_results
    )

    # 打印结果摘要
    print("\n处理完成!")