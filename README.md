# 🚀 arXivAgent

<div align="center">

**基于多模态解析和大模型的 arXiv 论文智能分析助手**

支持论文抓取、PDF解析、图表理解、自动摘要生成与可视化展示，帮助研究人员快速获取最新研究动态。

</div>

---

## 项目结构

```
arXivAgent/
│
├── app.py                  # Flask Web 入口
├── main.py                 # CLI 入口
├── config.py               # 配置管理（环境变量）
├── download_minerU.py      # MinerU 模型下载脚本
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
│
├── api/
│   ├── __init__.py
│   └── flask_app.py        # Flask API 应用工厂 + 路由
│
├── core/
│   ├── __init__.py
│   ├── paper_searcher.py   # arXiv API 论文搜索
│   ├── pdf_processor.py    # PDF 下载 + MinerU 解析
│   └── summarizer.py       # LLM 摘要生成
│
├── services/
│   ├── __init__.py
│   └── paper_service.py    # 服务整合层（流式/批量）
│
├── utils/
│   ├── __init__.py
│   ├── file_utils.py       # 文件与目录工具
│   ├── text_utils.py       # 文本处理工具
│   └── oss_utils.py        # 阿里云 OSS 上传
│
└── templates/
    └── index.html          # Web 前端界面
```

## 功能特性

| 特性 | 说明 |
|------|------|
| **智能论文检索** | 按领域、关键词、时间范围搜索 arXiv 论文，支持多关键词组合 |
| **PDF 自动解析** | 基于 MinerU 解析 PDF，支持文本模式与 OCR 模式，提取正文、公式、图表 |
| **多模态理解** | 结合大模型分析论文内容与图表，支持图片上传至 OSS 供模型引用 |
| **自动摘要生成** | 生成中文摘要、创新点总结、方法分析、图表解读与实验结论 |
| **流式实时响应** | Web 端 SSE 流式传输处理进度，前端实时展示每篇论文结果 |
| **结果本地缓存** | 搜索结果 24h 内自动缓存至 localStorage，重复访问无需重新分析 |
| **Web 可视化界面** | 交互式论文浏览与参数配置界面，支持 Markdown 渲染与代码高亮 |
| **阿里云 OSS 存储** | 解析结果与图片资源自动上传 OSS，生成可公开访问的链接 |
| **CLI 模式** | 支持命令行批量处理，适合脚本集成 |

## 快速开始

### 1. 克隆项目

```bash
git clone git@github.com:kuguyvk/arXivAgent.git
cd arXivAgent
```

### 2. 下载 MinerU 模型

```bash
python download_minerU.py
```

如需 GPU 加速，修改 `C:/Users/用户名/magic-pdf.json` 中的 `"device-mode": "cpu"` 为 `"device-mode": "cuda"`。

### 3. 安装依赖

建议使用 Conda 虚拟环境：

```bash
conda create -n arxivagent python=3.10
conda activate arxivagent
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env`，并填入配置：

```env
API_BASE=https://api.deepseek.com          # API 地址
API_KEY=your_api_key_here                   # API Key

OSS_ACCESS_KEY_ID=your_key_id               # 阿里云 OSS 配置（可选）
OSS_ACCESS_KEY_SECRET=your_key_secret
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your_bucket

FLASK_PORT=5000
FLASK_DEBUG=True
```

**注意：** Web 模式下 API Key 通过前端页面传入，不强制要求 `.env` 中配置 `API_KEY`。

### 5. 启动项目

**Web 模式：**

```bash
python app.py
```

访问 `http://localhost:5000`

**CLI 模式：**

```bash
python main.py \
    --api_key your_key \
    --api_base https://api.deepseek.com \
    --model_name deepseek-chat \
    --category cs.CV \
    --keyword emotion \
    --date_from 20250501 \
    --date_to 20250518 \
    --max_results 5
```

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端框架 | Flask |
| 大模型 | OpenAI 兼容 API / Google Gemini API |
| PDF 解析 | MinerU（支持文本 + OCR 双模式） |
| 前端 | HTML + CSS + JavaScript |
| Markdown 渲染 | marked.js + highlight.js |
| 对象存储 | 阿里云 OSS |
| 论文数据源 | arXiv API |

## 项目演示 📽️

[![arXivAgent example video - YouTube](https://res.cloudinary.com/marcomontalbano/image/upload/v1779075699/video_to_markdown/images/youtube--C3a2PMurxfE-c05b58ac6eb4c4700831b2b3070cd403.jpg)](https://www.youtube.com/watch?v=C3a2PMurxfE "arXivAgent example video - YouTube")

## TODO

- [ ] 支持更多大模型
- [ ] 支持本地 LLM 推理
- [ ] 支持向量数据库检索
- [ ] 支持 RAG 问答

## 致谢

- [arXiv](https://arxiv.org/)
- [MinerU](https://github.com/opendatalab/MinerU)
- [Flask](https://flask.palletsprojects.com/)