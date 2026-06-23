# Spec: 文本词频分析与可视化系统 v2

> 基于现有 `app.py` 重构，面向课程设计作业交付。
> v1.1 — 经 doubt-driven-development 对抗性审查修正

---

## Objective

将基础的中文分词可视化工具（仅支持 URL 输入、单一图表）升级为**功能完整 + 界面精致**的课程设计作品。

- **用户:** 课程设计提交者本人
- **核心价值:** 多入口输入文本 → 中文分词 → 词频统计 → 多图表可视化 → 结果持久化可回溯可对比
- **Success:** 四种输入方式均可正常使用、历史记录跨会话持久保存、两篇文本词频可对比、界面达到成品级别

### 用户故事

| # | 故事 | 验收条件 |
|---|------|---------|
| US1 | 我可以粘贴一段中文文本，立即看到分词和词频图表 | 粘贴 → 触发分析 → 图表出现 |
| US2 | 我可以上传本地 TXT/MD 文件进行分析 | 选择文件 → 自动加载内容 → 分析 |
| US3 | 我可以输入 URL 抓取网页文本分析（已有，保留） | URL → Enter → 分析 |
| US4 | 我可以查看过往的分析记录，点击某条恢复查看 | 历史列表可浏览，点击加载 |
| US5 | 我可以选择两条历史记录进行词频对比 | 选两条 → 对比视图 |

---

## Tech Stack

| 层 | 技术 | 版本 |
|----|------|------|
| Web 框架 | Streamlit | ≥1.32.0 |
| 中文分词 | jieba | ≥0.42.1 |
| 图表 | pyecharts + streamlit-echarts | pyecharts≥2.0.5, s-e≥0.4.0 |
| 网页抓取 | requests + BeautifulSoup | 见 requirements.txt |
| 持久化 | JSON 文件 | Python stdlib（`json`） |
| 文本处理 | re（内置） | — |

**无新增依赖** — 版本与现有 `requirements.txt` 一致，所有功能用现有依赖 + Python 标准库实现。

---

## Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
streamlit run app.py

# 指定端口启动
streamlit run app.py --server.port 8501
```

---

## Project Structure

```
text-analysis-app/
├── app.py                  # Streamlit 主入口（UI 编排，不含业务逻辑实现）
├── requirements.txt        # Python 依赖
├── SPEC.md                 # 本规格文档
├── TASKS.md                # 任务拆分（Plan 阶段产出）
├── modules/                # 业务逻辑模块（纯 Python，不含 Streamlit 导入）
│   ├── __init__.py
│   ├── text_input.py       # 多入口文本获取（URL / 上传 / 粘贴）
│   ├── text_cleaner.py     # 文本清洗 + 正则 + 编码检测
│   ├── segmenter.py        # jieba 分词 + 过滤
│   ├── statistics.py       # 词频统计
│   ├── charts.py           # 图表生成（7 种图表）
│   └── history.py          # 历史记录读写（JSON 持久化 + 初始化）
├── data/                   # 运行时数据（首次运行自动创建）
│   └── history.json        # 历史记录持久化文件
├── tests/                  # 测试
│   └── test_*.py
└── 课程设计报告模板_词频分析可视化系统.md
```

**拆分原则:** 每个 `modules/*.py` 是纯 Python 模块，不含 Streamlit UI 代码。`app.py` 只负责 UI 编排（调用模块函数、渲染结果），不包含算法实现。`app.py` 中"业务逻辑实现"指字符串处理、正则、分词、统计算法的具体代码——简单的管线调用链（`f1() → f2() → f3()`）不算业务逻辑。

---

## Streamlit Session State 管理

Streamlit 每次交互重新执行全脚本，跨 rerun 的状态必须显式管理。

### Session State 键设计

| 键名 | 类型 | 用途 | 初始化 |
|------|------|------|--------|
| `current_tab` | `str` | 当前活跃输入 Tab（"url" / "upload" / "paste"）| `"url"` |
| `url_input` | `str` | URL 输入框内容 | `""` |
| `paste_input` | `str` | 粘贴文本区内容 | `""` |
| `uploaded_content` | `str` | 上传文件的文本内容 | `""` |
| `uploaded_filename` | `str` | 上传文件名 | `""` |
| `analysis_result` | `dict \| None` | 当前分析结果（含 top20, all_freq 等） | `None` |
| `selected_history_ids` | `list[str]` | 对比模式中选中的历史记录 ID | `[]` |
| `viewing_history_id` | `str \| None` | 当前正在查看的历史记录 ID | `None` |

### 状态生命周期

- 切换 Tab 时：不清空其他 Tab 的 session state 值（保留跨 Tab 输入内容）
- 分析完成时：将结果写入 `analysis_result`，同时存入 `history.json`
- 查看历史时：`viewing_history_id` 设为该记录 ID，图表区切换为历史回看模式
- 退出对比时：清空 `selected_history_ids` 和 `viewing_history_id`
- 清空历史时：弹出确认对话框，确认后清空文件并重置相关 session state

### UX 护栏

- **未输入提示:** 当前活跃 Tab 无有效内容时，页面显示"请先输入文本"提示，不渲染空图表
- **活跃 Tab 指示:** 当前活跃 Tab 使用 Streamlit 原生高亮，输入区下方显示当前分析将使用的输入来源说明文字
- **分析触发:** URL 用 Enter 或"开始分析"按钮；粘贴用"开始分析"按钮；上传文件选择后自动触发

---

## Code Style

```python
# 模块风格示例：text_cleaner.py

import re
from typing import Tuple

def detect_and_read(uploaded_file) -> Tuple[str, str]:
    """
    检测文件编码并读取内容。优先 UTF-8，失败回退 GBK。

    Args:
        uploaded_file: Streamlit UploadedFile 对象

    Returns:
        (text_content, encoding_used)

    Raises:
        ValueError: 两种编码均无法解码
    """
    raw_bytes = uploaded_file.read()
    for encoding in ("utf-8", "gbk"):
        try:
            return raw_bytes.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法以 UTF-8 或 GBK 解码文件: {uploaded_file.name}")


def clean_text(raw: str) -> str:
    """
    清洗原始文本：去多余空白、保留中文/数字/字母/常用标点。

    Args:
        raw: 原始文本字符串

    Returns:
        清洗后的文本
    """
    text = ' '.join(raw.split())
    text = re.sub(
        r'[^一-龥a-zA-Z0-9，。！？；：""''（）【】《》、·]',
        '', text
    )
    return text
```

- **命名:** 模块 `snake_case.py`，函数 `snake_case()`，类 `PascalCase`
- **类型注解:** 所有公开函数参数和返回值加类型注解
- **文档字符串:** 每个公开函数用 Google-style docstring（Args / Returns / Raises）
- **注释:** 解释"为什么"，不解释"是什么"
- **模块职责:** 一个模块只做一件事；UI 代码只在 `app.py`
- **`app.py` 业务逻辑限制:** `app.py` 中单个函数体内不得写超过 50 行的算法实现逻辑。管线调用（`a(); b(); c()`）和 Streamlit 组件渲染不计入

---

## Testing Strategy

- **框架:** pytest
- **测试范围:** 纯逻辑模块（text_cleaner, segmenter, statistics, history）
- **不测试:** Streamlit UI 层、pyecharts 图表渲染（属于框架测试范畴）
- **覆盖率目标:** 核心模块 ≥80% 行覆盖
- **测试隔离:**
  - `text_cleaner` / `segmenter` / `statistics`: 纯函数，可直接测试
  - `history`: 使用 pytest `tmp_path` fixture 创建临时 JSON 文件，**禁止**直接操作 `data/history.json`（避免破坏用户数据）

---

## Architecture: Data Flow

```
用户输入（URL/上传/粘贴）
        │
        ▼
  text_input.py        ─── 返回 raw_text: str
        │                    URL: requests.get + BeautifulSoup
        │                    上传: detect_and_read(UTF-8→GBK fallback)
        │                    粘贴: 直接取 text_area 内容
        │
        ▼
  text_cleaner.py      ─── 返回 cleaned_text: str
        │
        ▼
  segmenter.py         ─── 返回 words: list[str]（已过滤单字和空白）
        │
        ▼
  statistics.py        ─── 返回 [(word, freq), ...]
        │
        ├──→ history.py      ─── 保存到 data/history.json
        │
        └──→ charts.py       ─── 生成 pyecharts 图表对象
                 │
                 ▼
            app.py (st_pyecharts 渲染)
```

---

## UI Layout（重构后）

```
┌─────────────────────────────────────────────────┐
│  📊 文本词频分析与可视化系统                      │ ← 标题区
│  [URL 输入] [上传文件] [粘贴文本]                 │ ← Tabs（当前活跃高亮）
│  📌 当前将分析来自「URL 输入」的文本               │ ← 活跃 Tab 指示
├──────────────────────┬──────────────────────────┤
│  🧩 参数控制面板      │                          │
│  (侧边栏)            │     可视化结果区域         │
│                      │                          │
│  ┌ 图表类型 ───────┐ │   ┌──────────────────┐   │
│  │ ○ 词云图        │ │   │                  │   │
│  │ ○ 柱状图        │ │   │   图 表 区       │   │
│  │ ○ 横向柱状图    │ │   │                  │   │
│  │ ○ 折线图        │ │   └──────────────────┘   │
│  │ ○ 面积图        │ │                          │
│  │ ○ 饼图          │ │                          │
│  │ ○ 雷达图        │ │                          │
│  └─────────────────┘ │   ┌─────────────────────┐│
│  ┌ 最低词频 ──────┐  │   │  📋 Top20 表格        ││
│  │ [===slider====] │  │   └─────────────────────┘│
│  └─────────────────┘  │                          │
├──────────────────────┴──────────────────────────┤
│  📜 历史记录（按时间倒序）       [清空全部历史]     │ ← 底部折叠面板
│  ┌──────────────────────────────────────────┐   │
│  │ ☐ 2024-06-23 14:30  🔗 URL: xxx.com     │   │
│  │    Top: 中国(42) 发展(38) 经济(35)...     │   │
│  │ ☐ 2024-06-23 14:25  📄 news1.txt        │   │
│  │    Top: 人工智能(56) 技术(41)...          │   │
│  └──────────────────────────────────────────┘   │
│  [对比选中记录]  ← 仅当恰好勾选 2 条时可用         │
│  ┌──────────────────────────────────────────┐   │
│  │          📊 对比视图（叠加柱状图）          │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 功能规格

### F1: 多输入方式

| 输入方式 | 交互组件 | 输出 |
|---------|---------|------|
| URL | `st.text_input` + "开始分析"按钮 | 抓取网页 → 提取文本 |
| 上传文件 | `st.file_uploader`，接受 `.txt` `.md` | 读取文件内容（UTF-8 → GBK fallback） |
| 粘贴文本 | `st.text_area` + "开始分析"按钮 | 直接用粘贴内容 |

- **互斥与保留:** 三种方式通过 Tabs 切换。切换 Tab 时通过 `st.session_state` 保留各 Tab 的输入内容。每次分析仅使用当前活跃 Tab 的输入。
- **管线复用:** 文本清洗 + 分词 + 统计 + 图表 管线在所有输入方式间完全复用。
- **空输入处理:** 当前活跃 Tab 无有效内容时，图表区显示提示文字"请在当前 Tab 输入文本后点击「开始分析」"，不渲染空图表。
- **上传文件编码:** 优先 UTF-8 解码，失败则尝试 GBK（覆盖 Windows 中文环境常见场景）。两种编码均失败时 `st.error` 提示用户。

### F1-补充: URL 抓取错误处理

URL 输入必须覆盖以下错误场景，均以 `st.error` 中文提示用户，**不暴露 traceback**：

| 错误场景 | 处理方式 |
|---------|---------|
| DNS 解析失败 / 网络不通 | `requests.ConnectionError` → "无法连接到服务器，请检查 URL 是否正确" |
| HTTP 4xx/5xx | `requests.HTTPError` / 状态码检测 → "服务器返回错误（{code}），请检查链接是否有效" |
| 请求超时 | `requests.Timeout`（timeout=10s）→ "请求超时，请检查网络或稍后重试" |
| 非 HTML 内容（PDF/图片/JSON） | `Content-Type` 检测 → "该链接不是可解析的网页文本" |
| 编码检测 | `response.apparent_encoding`（保留现有逻辑） |

### F2: 历史记录

- **存储格式:** JSON 数组，每条记录包含：
  ```json
  {
    "id": "<uuid4>",
    "timestamp": "2024-06-23T14:30:00",
    "source_type": "url | upload | paste",
    "source_label": "https://... 或 文件名 或 '手动粘贴'",
    "text_preview": "前100个字符...",
    "total_words": 12345,
    "vocabulary_size": 2345,
    "top20": [["词语", 频次], ...],
    "chart_type": "词云图",
    "min_freq": 2
  }
  ```
  - `chart_type`: 记录分析时用户选中的图表类型。加载历史记录时自动切换到该类型渲染。
  - `min_freq`: 记录分析时使用的词频阈值。用于对比时提示阈值差异。
- **存储位置:** `data/history.json`
- **文件初始化:** 首次运行（或文件被误删）时，`history.py` 自动创建 `data/` 目录和空数组 `[]` 的 `history.json`，不抛异常。
- **容量限制:** 最多保留 50 条。第 51 条写入时自动删除时间戳最旧的记录（FIFO）。
  - 对比时已加载到内存的数据不受删除影响（对比加载时复制数据，不依赖实时文件读取）。
- **操作:**
  - 浏览：按时间倒序列表，每条显示时间、来源图标、来源标签、Top3 词
  - 查看：点击某条 `📂 查看` 按钮 → 图表区切换为该记录的历史回看（还原 chart_type 和 top20 数据），此时侧边栏图表类型跟随切换
  - 删除：每条记录有 `🗑 删除` 按钮；顶部有"清空全部历史"按钮（弹出确认对话框）
  - 退出回看：点击"返回当前分析"按钮恢复实时分析视图

### F3: 文本对比

- **触发:** 在历史记录列表中勾选恰好 2 条 → 点击"对比选中记录"按钮
  - 勾选 0 条或 1 条：按钮灰色禁用，提示"请勾选 2 条记录进行对比"
  - 勾选 ≥3 条：按钮灰色禁用，提示"最多选择 2 条记录"
- **展示:**
  - 并排双栏表格：左文本 A Top20，右文本 B Top20（各显示来源标签和词频阈值）
  - 叠加柱状图：X 轴 = 两文本 Top20 词汇的并集，两组柱子（蓝色/橙色）区分文本
  - 图表标题标明两文本来源
- **阈值不一致提示:** 若两条记录的 `min_freq` 不同，对比视图顶部用 `st.info` 标明差异（"注意：文本 A 词频阈值={a}，文本 B 词频阈值={b}，Top20 对比不完全对等"）
- **边界:** 只对比 Top20；不对比全量词频（性能 + 可读性）

### F4: UI 重构

- **布局:** 保留侧边栏放控制参数；主区域用 Tabs 切换输入方式
- **视觉:**
  - Streamlit 原生色调为主（蓝/灰/白），图表使用 pyecharts 内置配色
  - 历史记录用卡片式展示（`st.container` + 分隔线），每条突出时间戳和 Top3 关键词
  - 折叠面板收纳清洗后文本和全量词频（保留现有 expander 设计）
- **响应:** 图表区占主区域宽度的 ≥60%，表格自适应；桌面端优先（笔记本演示场景），不强制移动端适配
- **状态提示:**
  - 抓取/分析中：`st.spinner("正在分析文本...")`
  - 分析成功：`st.toast("✅ 分析完成")`（Streamlit ≥1.32 支持）
  - 分析失败：`st.error()` 中文提示，不暴露 traceback

---

## 7 种图表类型

| # | 图表类型 | pyecharts 类 | 说明 |
|---|---------|-------------|------|
| 1 | 词云图 | `WordCloud` | Top20 词频，字号映射词频 |
| 2 | 柱状图 | `Bar` | 垂直柱状，X 轴标签旋转 45° |
| 3 | 横向柱状图 | `Bar` + `reversal_axis()` | 横向排列，内置 DataZoom |
| 4 | 折线图 | `Line` | X 轴标签旋转 45° |
| 5 | 面积图 | `Line` + `AreaStyleOpts` | 折线下方半透明填充 |
| 6 | 饼图 | `Pie` | 环形饼图，标签外置 |
| 7 | 雷达图 | `Radar` | 仅取 Top6（pyecharts 雷达图维度限制） |

---

## Success Criteria

| # | 条件 | 验证方式 |
|---|------|---------|
| SC1 | URL 输入 → 分析 → 图表展示，全流程无报错；无效 URL 有中文错误提示 | 手动测试有效 URL + 无效 URL |
| SC2 | 上传 `news1.txt`（UTF-8 和 GBK 编码各一份）→ 分词 → 图表正常 | 手动测试 |
| SC3 | 粘贴 200 字中文 → 点击"开始分析"→ 图表正常 | 手动测试 |
| SC4 | 分析完成后历史列表出现新记录，`history.json` 内容正确 | 检查文件 |
| SC5 | 关闭并重启 Streamlit，历史记录仍在；首次启动无 `history.json` 时不崩溃 | 重启后检查 |
| SC6 | 选 2 条历史 → 对比按钮可用 → 点击后叠加柱状图展示；选 0/1/3 条时按钮禁用 | 手动验收 |
| SC7 | 切换 7 种图表类型（词云/柱状/横向柱状/折线/面积/饼图/雷达）均正常渲染 | 逐一切换 |
| SC8 | 词频过滤滑块生效（改变阈值后图表和 Top20 表格更新）| 手动验收 |
| SC9 | 代码模块拆分清晰：`app.py` 不含业务逻辑实现，`modules/` 各模块职责单一 | 代码审查 |
| SC10 | 上传 GBK 编码 .txt 文件可正确解码并分析 | 手动测试 |
| SC11 | 首次运行（无 `data/` 目录）不崩溃，自动创建 `history.json` | 删除目录后启动 |
| SC12 | 历史记录超 50 条后自动删除最旧记录 | 手动验证 |

---

## Boundaries

### Always do
- 运行 `streamlit run app.py` 验证修改效果后再提交
- 新功能先拆模块再写 UI
- 保持现有清洗和分词逻辑不变（已验证可用）
- 所有用户可见文字用中文
- 文件编码检测：UTF-8 优先，GBK fallback

### Ask first
- 新增 pip 依赖（当前设计不需新增，如需则先讨论）
- 修改 `history.json` 数据格式（影响已有数据兼容性）
- 更改图表库（pyecharts → 其他）
- 调整 session state 键名（影响全局状态）

### Never do
- 在 `app.py` 中写超过 50 行的业务逻辑实现函数（管线调用链不计入）
- 硬编码文件路径（使用 `pathlib.Path(__file__).parent / "data"` 推导）
- 将 secrets/API key 写入代码
- 删除 `data/history.json` 而不弹出确认对话框
- 直接暴露 Python traceback 给用户（始终用 `st.error` 包裹）
- 测试中直接操作 `data/history.json`（用 `tmp_path` 隔离）

---

## Open Questions

_全部已解决，无遗留项。_

---

## Revision History

| 日期 | 变更 | 原因 |
|------|------|------|
| 2024-06-23 | v1.0 初始版本 | 基于 interview-me 产出 + 现有 app.py 分析 |
| 2024-06-23 | v1.1 对抗性审查修正 | doubt-driven-development：补充 session state 设计、错误处理分类、编码 fallback、空状态处理、历史初始化、对比边界、测试隔离、图表显式列表 |
