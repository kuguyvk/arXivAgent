import json
import os
import re
import oss2


class ImageUtils:
    """图片处理相关的工具函数"""

    @staticmethod
    def extract_image_paths(summary):
        """从大模型生成的摘要中提取图片路径"""
        img_paths = []

        # 匹配标准的Markdown图片语法
        img_pattern = re.compile(r'!\[\]\((.*?)\)')

        # 查找所有匹配的图片路径
        matches = img_pattern.findall(summary)

        # 过滤出有效的图片路径
        for path in matches:
            path = path.strip()
            if path:
                img_paths.append(path)
                print(f"提取到有效图片路径: {path}")
            else:
                print(f"忽略非本地图片路径: {path}")

        return img_paths


class OSSUploader:
    """阿里云OSS上传工具类"""

    def __init__(self, oss_config):
        """
        初始化OSS上传器

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

    def upload_to_oss(self, local_path, paper_title,output_dir):
        """上传文件到阿里云OSS"""
        if not self.oss_config:
            print("OSS配置未提供，跳过上传")
            return None
        if not os.path.exists(local_path):
            print(f"错误: 本地文件不存在 - {local_path}")
            return None

        try:
            # 清理文件名
            clean_title = re.sub(r'[^\w\-_. ]', '_', paper_title)
            clean_title = clean_title.replace(" ", "_")
            clean_title = clean_title[:100]

            # 生成OSS路径 - 保持相同的目录结构
            oss_path = f"{output_dir}/{clean_title}/{os.path.basename(local_path)}"

            print(f"上传到OSS: {local_path} -> {oss_path}")

            # 上传文件
            self.oss_bucket.put_object_from_file(oss_path, local_path)

            # 生成公共访问URL
            url = f"https://{self.oss_config['bucket_name']}.{self.oss_config['endpoint']}/{oss_path}"
            print(f"上传成功: {url}")
            return url

        except Exception as e:
            print(f"上传到OSS失败: {str(e)}")
            return None



class FileUtils:
    """文件处理相关的工具函数"""

    @staticmethod
    def clean_filename(filename, max_length=100):

        # 去掉特殊字符，保留空格
        clean_name = re.sub(r'[^\w\-_. ]', '_', filename)
        # 将空格替换为下划线
        clean_name = clean_name.replace(" ", "_")
        # 限制文件名长度
        clean_name = clean_name[:max_length]
        return clean_name

    @staticmethod
    def ensure_dir_exists(dir_path):

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    @staticmethod
    def create_directory_structure(base_dir, subdirs):
        """
        创建目录结构

        """
        FileUtils.ensure_dir_exists(base_dir)

        dir_paths = {}
        for subdir in subdirs:
            dir_path = os.path.join(base_dir, subdir)
            FileUtils.ensure_dir_exists(dir_path)
            dir_paths[subdir] = dir_path

        return dir_paths


class StringUtils:
    """字符串处理相关的工具函数"""

    @staticmethod
    def format_authors(authors):
        """
        格式化作者列表

        """
        author_names = []
        for author in authors:
            if hasattr(author, 'name'):
                author_names.append(author.name)
            else:
                author_names.append(str(author))

        return ', '.join(author_names)

def load_oss_config(config_path="oss_config.json"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"OSS配置文件未找到: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)



