#页面流式响应展示
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import  time
from agent import ArxivPaperSummarizer

app = Flask(__name__)
CORS(app)  # 允许跨域请求

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


def process_papers_stream(summarizer, query, max_results):
    """生成处理论文的流式响应"""
    try:
        # 搜索论文
        papers = summarizer.search_papers(query, max_results=max_results)
        total = len(papers)

        # 发送初始状态
        yield json.dumps({
            "type": "status",
            "message": f"找到 {total} 篇论文，开始处理...",
            "total": total,
            "processed": 0
        }) + "\n"

        # 处理每篇论文
        for i, paper in enumerate(papers):
            # 发送开始处理通知
            yield json.dumps({
                "type": "status",
                "message": f"正在处理论文 {i + 1}/{total}: {paper.title[:50]}...",
                "total": total,
                "processed": i,
                "current": i + 1
            }) + "\n"

            try:
                # 下载PDF
                pdf_path = summarizer.download_paper(paper)

                # 转换markdown提取图表
                markdown_path, json_path = summarizer.minerU_analysis(pdf_path)

                # 生成摘要
                summary = summarizer.generate_summary(paper, markdown_path, json_path)

                # 保存摘要
                result = summarizer.save_summary(paper, summary)

                # 处理作者列表
                author_names = []
                for author in paper.authors:
                    if hasattr(author, 'name'):
                        author_names.append(author.name)
                    else:
                        author_names.append(str(author))

                # 发送处理完成的论文
                yield json.dumps({
                    "type": "paper",
                    "data": {
                        "title": paper.title,
                        "authors": author_names,
                        "published": str(paper.published),
                        "markdown_content": result,
                        "success": True
                    },
                    "processed": i + 1,
                    "total": total
                }) + "\n"

            except Exception as e:
                print(f"处理论文时出错: {str(e)}")
                # 发送错误信息
                yield json.dumps({
                    "type": "paper",
                    "data": {
                        "title": paper.title,
                        "authors": [],
                        "success": False,
                        "error": str(e)
                    },
                    "processed": i + 1,
                    "total": total
                }) + "\n"

            # 添加延迟以避免API限制
            time.sleep(2)

        # 发送完成通知
        yield json.dumps({
            "type": "complete",
            "message": "所有论文处理完成",
            "processed": total,
            "total": total
        }) + "\n"

    except Exception as e:
        yield json.dumps({
            "type": "error",
            "message": f"处理过程中出错: {str(e)}"
        }) + "\n"


@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    try:
        api_key = data['apiKey']
        category = data['category']
        keyword = data['keyword']
        date_from = data['dateFrom'].replace('-', '')
        date_to = data['dateTo'].replace('-', '')
        max_results = int(data['maxResults'])

        query = f"cat:{category} AND all:{keyword} AND submittedDate:[{date_from} TO {date_to}]"
        output_dir=f"{date_from}-{date_to}_{category.replace('.', '')}_{keyword}"

        summarizer = ArxivPaperSummarizer(
            api_key=api_key,
            output_dir=output_dir
        )
        return Response(
            process_papers_stream(summarizer, query, max_results),
            mimetype='text/event-stream'
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
