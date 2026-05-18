"""
Flask API 模块
提供 Web 服务和流式响应
"""
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import logging

from utils.file_utils import FileUtils
from config import Config
from services.paper_service import PaperService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_app():
    """创建 Flask 应用工厂函数"""
    app = Flask(__name__)
    CORS(app)  # 允许跨域请求

    # 注册路由
    register_routes(app)

    return app


def register_routes(app):
    """注册路由"""

    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    def process_papers_stream(summarizer, query, max_results):
        """生成处理论文的流式响应"""
        # 直接使用 PaperService 的流式处理方法
        yield from summarizer.process_papers_stream(query, max_results)

    @app.route('/summarize', methods=['POST'])
    def summarize():
        """处理论文摘要请求"""
        try:
            data = request.json

            # 提取参数
            api_key = data.get('apiKey')
            base_url = data.get('apiBase')
            model_name = data.get('modelName')
            category = data.get('category')
            keyword = data.get('keyword')
            date_from = data.get('dateFrom', '').replace('-', '')
            date_to = data.get('dateTo', '').replace('-', '')
            max_results = int(data.get('maxResults', Config.MAX_RESULTS_DEFAULT))

            # 验证必填参数
            if not all([api_key, category, keyword, date_from, date_to]):
                return jsonify({
                    "status": "error",
                    "message": "缺少必填参数"
                }), 400

            # 构建查询
            query = f"cat:{category} AND all:{keyword} AND submittedDate:[{date_from} TO {date_to}]"
            output_dir = FileUtils.auto_output_dir(category, keyword, date_from, date_to)


            # 初始化服务
            summarizer = PaperService(
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
                output_dir=output_dir,
                oss_config=Config.OSS_CONFIG
            )

            # 返回流式响应
            return Response(
                process_papers_stream(summarizer, query, max_results),
                mimetype='text/event-stream'
            )

        except Exception as e:
            logger.error(f"处理请求失败：{str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    # 运行 Flask 应用
    app.run(port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
