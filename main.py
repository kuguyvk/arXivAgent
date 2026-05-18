"""
arXiv 论文摘要生成工具 - CLI 入口
"""
import argparse
import logging
import sys

from config import Config
from services.paper_service import PaperService
from utils.file_utils import FileUtils


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='arXiv 论文摘要生成工具')
    parser.add_argument(
        '--api_key',
        type=str,
        required=True,
        help="Gemini API Key"
    )
    parser.add_argument(
        '--api_base',
        type=str,
        default=Config.API_BASE,
        help='API 基础 URL'
    )
    parser.add_argument(
        '--model_name',
        type=str,
        default=Config.MODEL_NAME,
        help='使用的模型名称'
    )
    parser.add_argument(
        '--max_results',
        type=int,
        required=True,
        help='最大处理论文数量'
    )
    parser.add_argument(
        '--category',
        type=str,
        required=True,
        help='论文领域，如 cs.CV'
    )
    parser.add_argument(
        '--keyword',
        type=str,
        required=True,
        help='搜索关键词，如 emotion'
    )
    parser.add_argument(
        '--date_from',
        type=str,
        required=True,
        help='起始日期，如 20250518'
    )
    parser.add_argument(
        '--date_to',
        type=str,
        required=True,
        help='结束日期，如 20250520'
    )


    args = parser.parse_args()

    # 分离关键词列表
    keywords = [k.strip() for k in args.keyword.split(',') if k.strip()]    
    keyword = " AND ".join([f'all:"{k}"' for k in keywords])


    # 构建查询
    query = f'cat:{args.category} AND ({keyword}) AND submittedDate:[{args.date_from} TO {args.date_to}]'

    # 确定输出目录

    output_dir = FileUtils.auto_output_dir(args.category, args.keyword, args.date_from, args.date_to)

    logger.info(f"输出目录：{output_dir}")

    try:
        # 初始化论文服务
        summarizer = PaperService(
            api_key=args.api_key,
            base_url=args.api_base,
            model_name=args.model_name,
            output_dir=output_dir,
            oss_config=Config.OSS_CONFIG
        )

        # 处理论文
        results = summarizer.process_papers(
            query=query,
            max_results=args.max_results
        )

        # 打印结果摘要
        success_count = sum(1 for r in results if r.get('success', False))
        logger.info(f"\n处理完成！成功：{success_count}/{len(results)}")

        # 返回退出码
        sys.exit(0 if success_count > 0 else 1)

    except Exception as e:
        logger.error(f"程序执行失败：{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
