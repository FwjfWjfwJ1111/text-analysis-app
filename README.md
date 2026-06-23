# 文本词频分析与可视化系统

基于 Streamlit 框架开发的词频分析可视化系统，支持多种输入方式和图表展示。

## 功能特性

- **多输入方式**：URL 抓取、文件上传、文本粘贴
- **7 种可视化图表**：词云图、柱状图、横向柱状图、折线图、面积图、饼图、雷达图
- **文本对比**：支持两条记录的词频对比分析
- **历史记录**：自动保存分析记录，支持查看/删除/清空

## 技术栈

- Python 3.10+
- Streamlit
- jieba（中文分词）
- pyecharts（可视化）
- wordcloud（词云）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

## 项目结构

```
text-analysis-app/
├── app.py                    # 主应用入口
├── modules/
│   ├── fetch_web.py          # URL 抓取与文件读取
│   ├── text_clean_token.py   # 文本清洗与分词
│   ├── chart_factory.py      # 图表生成工厂
│   └── history.py            # 历史记录管理
├── tests/                    # 单元测试
├── data/                     # 数据目录
└── docs/                     # 文档
```
