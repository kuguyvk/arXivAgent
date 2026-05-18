# arXivAgent 使用说明文档

## 1. 项目介绍

arXivAgent 是一个基于大模型和数据挖掘技术的论文助手，能够按照指定条件抓取、分析、总结 arXiv 论文，并通过可视化界面展示关键内容，帮助科研人员快速获取最新研究动态和趋势。

项目主要功能包括：

- 根据指定条件下载和解析 arXiv 论文元数据及全文
- 利用 MinerU 模型进行论文内容挖掘和摘要生成
- 交互式界面，方便用户查询和管理关注论文

### 视频演示

[![arXivAgent example video - YouTube](https://res.cloudinary.com/marcomontalbano/image/upload/v1750208970/video_to_markdown/images/youtube--w4jNM3CX9F0-c05b58ac6eb4c4700831b2b3070cd403.jpg)](https://www.youtube.com/watch?v=w4jNM3CX9F0 "arXivAgent example video - YouTube")
*演示视频*

---

## 2. 前期准备

### 2.1 克隆代码库

```bash
git clone git@github.com:kuguyvk/arXivAgent.git
cd arXivAgent
```

### 2.2 下载 MinerU 模型

运行 `download_minerU.py` 文件：

```bash
python download_minerU.py
```

- 可更改文件中的模型本地安装路径
- 如果想使用 GPU 加快推理速度，在模型成功下载后可在 `C:/Users/username/magic-pdf.json` 文件中更改 `"device-mode"` 为 `"cuda"`

### 2.3 环境配置

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 配置 OSS 云存储

1. 在阿里云上开通 OSS 对象存储
2. 创建 Bucket 实例，读写权限需设置为公共读
3. 创建之后在 `oss_config.json` 文件中配置

#### 获取 API Key

在 Gemini 官网获取 API_Key https://ai.google.dev/gemini-api/docs?hl=zh-cn

---

## 3. 运行

```bash
python app.py
```

启动后打开浏览器访问：http://localhost:5000
