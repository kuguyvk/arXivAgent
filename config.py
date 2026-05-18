"""
配置文件管理模块
集中管理所有配置项，支持环境变量覆盖
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""

    # API 配置,建议通过环境变量设置
    API_BASE = os.getenv("API_BASE", "api base url here")
    API_KEY = os.getenv("API_KEY", "your api key here") 
    MODEL_NAME = os.getenv("MODEL_NAME", "your model name here")

    # OSS 配置,建议通过环境变量设置
    OSS_CONFIG = {
        'access_key_id': os.getenv("OSS_ACCESS_KEY_ID", "your access key id here"),
        'access_key_secret': os.getenv("OSS_ACCESS_KEY_SECRET", "your access key secret here"),
        'endpoint': os.getenv("OSS_ENDPOINT", "your oss endpoint here"),
        'bucket_name': os.getenv("OSS_BUCKET_NAME", "your oss bucket name here")
    }

    # 目录配置
    DEFAULT_OUTPUT_DIR = "papers"
    PDF_SUBDIR = "pdfs"
    MARKDOWN_SUBDIR = "markdowns"
    IMAGE_SUBDIR = "images"
    SUMMARY_SUBDIR = "summaries"

    # 处理配置
    MAX_RESULTS_DEFAULT = 5
    API_RETRY_DELAY = 2  # 秒
    DOWNLOAD_TIMEOUT = 30  # 秒

    # Flask 配置
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"


class PromptTemplates:
    """提示词模板类"""

    @staticmethod
    def get_analysis_prompt(title, authors_str, published_date):
        """获取论文分析提示词模板"""
        return f"""我给你的是一篇学术论文的 markdown 文档以及相应的 json 文件，还有从论文中提取出的图表，请你帮我做以下分析：
1. 用中文总结论文的主要贡献和创新点（200 字以内）
2. 列出论文使用的主要方法和技术
3. 分析这篇论文的实验结果
4. 如果论文中有图表，请从该论文中选出几张最重要的图或者表，分别进行简要分析（最多不超过三张）

**重要说明：** 在插入图片时，请严格按照以下要求：
- 从 json 文件中找到对应图表的 img_path 字段
- **直接使用 json 文件中的 img_path 的值，必须逐字符复制该字段的值，不要添加任何前缀、后缀或修改路径**
- img_path 示例格式：General-purpose_audio_representation_learning_for_real-world_sound_scenes/a8c56e770318044471c290ecde37f586a95fcc8649715aeeddcaf034243f6e4b.jpg
- **禁止在路径前添加任何目录前缀（如 images/、../images/等）**

每张图表分析请严格按照下面格式输出，包括缩进、标点、符号和换行：
    *   **最有价值的图:**
        *   标题
        *   ![](【直接使用 json 中的 img_path 值】)
        *   **分析:**

5. 总结这篇论文

论文标题：{title}
论文作者：{authors_str}
发表日期：{published_date}
        """
