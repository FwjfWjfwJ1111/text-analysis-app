# Implementation Plan: 文本词频分析与可视化系统 v2

> 基于 [SPEC.md](./SPEC.md) v1.1 + [API 接口设计](#) 拆分全阶段任务。
> 适配《软件创新思维训练》课程设计报告 3.3 节开发计划。

---

## 架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 模块拆分粒度 | 4 纯逻辑模块 + 1 UI 编排 | 最小化 Streamlit 依赖面，纯模块可单独单测 |
| 图表工厂模式 | `ChartType` 枚举 → `create_chart()` 派发 | 消除 if-elif 链，新增图表类型 = 新增枚举值 + case 分支 |
| 持久化方案 | 单 JSON 文件，50 条 FIFO | 无 DB 依赖，课程作业本地演示零配置 |
| 状态管理 | `st.session_state` 8 键 | 跨 Streamlit rerun 保留 Tab 内容和分析结果 |
| 编码兼容 | UTF-8 → GBK fallback | 覆盖 Windows 中文环境常见场景 |

---

## 依赖关系图

```
B1 模块骨架
 │
 ├──→ B2 fetch_web ──────────────────────────────┐
 ├──→ B3 text_clean_token ───────────────────────┤
 ├──→ B4 chart_factory ──────────────────────────┤
 └──→ B5 history ────────────────────────────────┤
                                                  │
                    B6 app.py 重构 ←──────────────┘
                     │
                     ├──→ B7 多输入方式 + session state
                     │     │
                     │     └──→ B9 文本对比视图
                     │
                     ├──→ B8 历史记录面板
                     │
                     ├──→ B10 UI 视觉美化
                     └──→ B11 错误处理加固
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              Phase TEST            Phase REVIEW
               T1→T2→T3→T4→T5       R1 + R2
                    │                   │
                    └─────────┬─────────┘
                              ▼
                        Phase SHIP
                        S1→S2→S3
```

---

## 任务列表

---

### Phase 1: BUILD — Foundation（模块层）

#### Task B1: 创建模块目录结构

**描述:** 创建 `modules/` 包和 `data/`、`tests/` 目录，初始化 `__init__.py`。

**验收条件:**
- [ ] `modules/__init__.py` 存在
- [ ] `data/` 目录存在，含 `.gitkeep`
- [ ] `tests/__init__.py` 存在
- [ ] 项目目录结构符合 SPEC § Project Structure

**验证:** `python -c "import modules"` 无报错

**依赖:** 无

**涉及文件:**
- `modules/__init__.py`（新建）
- `data/.gitkeep`（新建）
- `tests/__init__.py`（新建）

**预计耗时:** 5 min | **规模:** XS

---

#### Task B2: 实现 `fetch_web.py` 模块

**描述:** 从现有 `app.py` 中提取 URL 抓取逻辑，新增 `read_uploaded_file()` 函数（含 UTF-8→GBK encoding fallback），定义 6 个 `FetchError` 异常子类。

**验收条件:**
- [ ] `fetch_url_text(url)` 返回清洗前纯文本，含完整异常处理
- [ ] `read_uploaded_file(raw_bytes, filename)` 支持 UTF-8 和 GBK 自动检测
- [ ] 6 个异常子类均含 `user_message` 属性
- [ ] 不导入 `streamlit`

**验证:**
```bash
python -c "from modules.fetch_web import fetch_url_text, read_uploaded_file, FetchError; print('OK')"
```

**依赖:** B1

**涉及文件:**
- `modules/fetch_web.py`（新建，约 60 行）

**预计耗时:** 40 min | **规模:** S

---

#### Task B3: 实现 `text_clean_token.py` 模块

**描述:** 从现有 `app.py` 中提取清洗正则 + jieba 分词 + Counter 统计逻辑，封装为 `clean_text()` → `segment_words()` → `filter_words()` → `count_and_rank()` 管线，提供一站式 `analyze()` 快捷函数。

**验收条件:**
- [ ] `clean_text(raw)` 保留中文字母数字和常用标点
- [ ] `segment_words(text)` 返回 jieba 精确模式分词列表
- [ ] `filter_words(words)` 过滤 len<2 和空白词
- [ ] `count_and_rank(words, min_freq)` 返回 `AnalysisResult` 数据类
- [ ] `analyze(raw_text, min_freq)` 端到端管线可用
- [ ] `EmptyTextError` 异常定义
- [ ] 不导入 `streamlit`

**验证:**
```bash
python -c "
from modules.text_clean_token import analyze
r = analyze('人工智能正在改变世界', min_freq=1)
print(r.top20)
"
```

**依赖:** B1

**涉及文件:**
- `modules/text_clean_token.py`（新建，约 80 行）

**预计耗时:** 30 min | **规模:** S

---

#### Task B4: 实现 `chart_factory.py` 模块

**描述:** 定义 `ChartType` 枚举，将 `app.py` 中 7 段 if-elif 图表分支提取为 `create_chart()` 工厂函数，每种图表类型一个内部 builder。

**验收条件:**
- [ ] `ChartType` 枚举含 7 个成员
- [ ] `create_chart(chart_type, top20, title)` 返回正确 pyecharts 对象
- [ ] 雷达图仅取前 6 项（pyecharts 限制）
- [ ] 空 `top20` 时抛出 `ChartFactoryError`
- [ ] 不导入 `streamlit`

**验证:**
```bash
python -c "
from modules.chart_factory import create_chart, ChartType
chart = create_chart(ChartType.WORD_CLOUD, [('中国', 10), ('发展', 8)], '测试')
print(type(chart).__name__)
"
```

**依赖:** B1

**涉及文件:**
- `modules/chart_factory.py`（新建，约 100 行）

**预计耗时:** 30 min | **规模:** S

---

#### Task B5: 实现 `history.py` 模块

**描述:** 实现历史记录的 JSON 文件读写、初始化、容量管理（50 条 FIFO）、单条删除、全量清空。

**验收条件:**
- [ ] `load_history()` — 读取 `data/history.json`；文件不存在时自动创建空 `[]`
- [ ] `save_record(record)` — 追加记录；超 50 条自动删除最旧
- [ ] `delete_record(record_id)` — 按 ID 删除单条
- [ ] `clear_all()` — 清空文件
- [ ] 文件路径通过 `pathlib.Path(__file__).parent` 推导
- [ ] 不导入 `streamlit`

**验证:**
```bash
python -c "
from modules.history import load_history, save_record, delete_record, clear_all
# 使用 tmp_path 测试
"
```

**依赖:** B1

**涉及文件:**
- `modules/history.py`（新建，约 80 行）

**预计耗时:** 40 min | **规模:** S

---

### Checkpoint: Foundation 完成

- [ ] 4 个纯逻辑模块均可独立 import 并运行
- [ ] 每个模块通过手动 smoke test
- [ ] 无模块导入 `streamlit`

---

### Phase 2: BUILD — Integration（UI 层）

#### Task B6: 重构 `app.py` 使用模块

**描述:** 将现有 `app.py` 的 `main()` 函数中业务逻辑调用替换为模块函数调用。保留现有 UI 结构和功能，但底层使用 `fetch_web`、`text_clean_token`、`chart_factory` 模块。**此任务只做替换，不加新功能。**

**验收条件:**
- [ ] 现有所有功能正常（URL 输入 → 分词 → 7 种图表）
- [ ] `app.py` 中无清洗正则、jieba 调用、Counter 操作
- [ ] `app.py` 中无 pyecharts 图表构造代码（只调用 `create_chart()`）
- [ ] 侧边栏参数控制正常
- [ ] 异常时 `st.error` 显示中文错误（不暴露 traceback）

**验证:** `streamlit run app.py` → 输入 URL → 验证所有图表

**依赖:** B2, B3, B4

**涉及文件:**
- `app.py`（重写，约 150 行 UI 编排）

**预计耗时:** 90 min | **规模:** M

---

#### Task B7: 实现多输入方式 + Session State

**描述:** 在 `app.py` 主区域添加 Tabs（URL / 上传文件 / 粘贴文本），通过 `st.session_state` 管理 8 个键的跨 rerun 状态。当前活跃 Tab 无内容时显示提示，切换 Tab 保留内容。

**验收条件:**
- [ ] URL Tab: 输入 + "开始分析"按钮，原有功能正常
- [ ] 上传 Tab: 接受 `.txt` `.md`，选择后自动读取并分词
- [ ] 粘贴 Tab: text_area + "开始分析"按钮
- [ ] 切换 Tab 不清空其他 Tab 内容
- [ ] 活跃 Tab 下方显示"当前将分析来自「XX」的文本"
- [ ] 空输入时图表区显示"请在当前 Tab 输入文本后点击「开始分析」"
- [ ] 上传 GBK 编码文件可正确解码

**验证:** 三个 Tab 逐一测试 + 上传项目已有 `news1.txt`

**依赖:** B6

**涉及文件:**
- `app.py`（修改 main 区域，约 60 行新增）

**预计耗时:** 60 min | **规模:** M

---

#### Task B8: 实现历史记录面板

**描述:** 在主区域底部添加历史记录折叠面板。每次分析完成自动保存，按时间倒序卡片式展示，支持查看/删除/清空。

**验收条件:**
- [ ] 分析完成后自动保存到 `history.json`
- [ ] 历史列表按时间倒序，每条显示时间/来源图标/Top3 词
- [ ] 点击"📂 查看"恢复该记录的图表和 Top20 表格
- [ ] 查看历史时侧边栏图表类型跟随还原
- [ ] 点击"🗑 删除"移除单条
- [ ] "清空全部历史"需要确认对话框
- [ ] 关闭重启 Streamlit 后历史仍在
- [ ] 首次运行（无 `data/` 目录）不崩溃

**验证:** 分析几条不同文本 → 重启 → 验证历史列表和回看功能

**依赖:** B5, B6

**涉及文件:**
- `app.py`（新增历史面板区域，约 70 行）
- `modules/history.py`（如有调整）

**预计耗时:** 60 min | **规模:** M

---

#### Task B9: 实现文本对比视图

**描述:** 从历史记录中勾选恰好 2 条 → "对比选中记录"按钮 → 并排双栏 Top20 + 叠加柱状图。

**验收条件:**
- [ ] 勾选 0 条或 1 条时对比按钮禁用，提示"请勾选 2 条记录"
- [ ] 勾选 ≥3 条时对比按钮禁用，提示"最多选择 2 条记录"
- [ ] 恰好 2 条时按钮可用
- [ ] 点击对比：并排显示两个 Top20 表格 + 叠加柱状图
- [ ] 两文本的 `min_freq` 不同时顶部 `st.info` 提示
- [ ] "退出对比"按钮恢复当前分析视图

**验证:** 分析 2 条不同文本 → 勾选对比 → 验证叠加柱状图和阈值提示

**依赖:** B8

**涉及文件:**
- `app.py`（新增对比区域和逻辑，约 60 行）

**预计耗时:** 45 min | **规模:** M

---

### Phase 3: BUILD — Polish（打磨）

#### Task B10: UI 视觉美化

**描述:** 统一配色方案、优化间距和排版、卡片式历史记录样式、改进标题和说明文字。

**验收条件:**
- [ ] 页面标题区域清晰，说明文字简洁
- [ ] 侧边栏控件排列整齐，说明信息可读
- [ ] 历史记录卡片式展示，分隔线清晰
- [ ] 图表区与表格区比例协调（图表 ≥60% 宽度）
- [ ] 全局使用 `st.spinner` 和 `st.toast` 反馈
- [ ] 所有用户可见文字为中文

**验证:** 视觉走查 → 各状态截图

**依赖:** B7, B8, B9

**涉及文件:**
- `app.py`（CSS 样式、布局调整，约 40 行新增）

**预计耗时:** 45 min | **规模:** M

---

#### Task B11: 错误处理加固

**描述:** 确保所有用户可见异常通过 `st.error`/`st.warning` 展示，不暴露 Python traceback。覆盖 SPEC § F1-补充 的 5 种 URL 错误场景。

**验收条件:**
- [ ] URL 连接失败 → 中文错误提示，不显示 traceback
- [ ] URL 404/500 → 中文错误提示
- [ ] URL 超时 → 中文错误提示
- [ ] URL 返回非 HTML → 中文错误提示
- [ ] 上传文件编码错误 → 中文错误提示
- [ ] 空文本 → "无有效中文内容"
- [ ] 未知异常 → "系统内部错误，请刷新页面重试"

**验证:** 输入无效 URL、非 HTML URL、故意超时 URL 逐一验证

**依赖:** B6

**涉及文件:**
- `app.py`（try/except 加固）
- `modules/fetch_web.py`（如有遗漏异常子类）

**预计耗时:** 30 min | **规模:** S

---

### Checkpoint: Integration 完成

- [ ] 全部 12 条 Success Criteria（SC1-SC12）通过验收
- [ ] 手动走查所有用户故事（US1-US5）

---

### Phase 4: TEST（测试）

#### Task T1: `text_clean_token.py` 单元测试

**描述:** 使用 pytest 测试清洗、分词、过滤、统计管线的确定性输入输出。

**验收条件:**
- [ ] 测试 `clean_text`：空白折叠、特殊字符移除、中文保留
- [ ] 测试 `segment_words`：基本分词结果
- [ ] 测试 `filter_words`：单字过滤、空白过滤
- [ ] 测试 `count_and_rank`：排序正确性、min_freq 过滤
- [ ] 测试 `analyze`：端到端管线，`AnalysisResult` 字段完整性
- [ ] 测试 `EmptyTextError`：空字符串、纯标点输入

**验证:** `pytest tests/test_text_clean_token.py -v`

**依赖:** B3

**涉及文件:**
- `tests/test_text_clean_token.py`（新建，约 50 行）

**预计耗时:** 30 min | **规模:** S

---

#### Task T2: `fetch_web.py` 单元测试

**描述:** 使用 `unittest.mock` 模拟 requests 响应，测试正常抓取和各类异常分支。

**验收条件:**
- [ ] Mock 正常 HTML 响应 → 返回提取文本
- [ ] Mock ConnectionError → 抛出 `FetchConnectionError`
- [ ] Mock HTTPError(404) → 抛出 `FetchHTTPError`
- [ ] Mock Timeout → 抛出 `FetchTimeoutError`
- [ ] Mock Content-Type: application/pdf → 抛出 `FetchContentTypeError`
- [ ] 测试 `read_uploaded_file` UTF-8 / GBK 解码

**验证:** `pytest tests/test_fetch_web.py -v`

**依赖:** B2

**涉及文件:**
- `tests/test_fetch_web.py`（新建，约 60 行）

**预计耗时:** 30 min | **规模:** S

---

#### Task T3: `history.py` 单元测试

**描述:** 使用 pytest `tmp_path` fixture 创建临时 JSON 文件，测试读写、初始化、容量限制、删除操作。

**验收条件:**
- [ ] 文件不存在时 `load_history()` 返回 `[]`
- [ ] `save_record()` 追加后文件内容正确
- [ ] 超 50 条自动删除最旧
- [ ] `delete_record()` 按 ID 删除
- [ ] `clear_all()` 清空
- [ ] 所有测试使用 `tmp_path`，不触碰真实 `data/history.json`

**验证:** `pytest tests/test_history.py -v`

**依赖:** B5

**涉及文件:**
- `tests/test_history.py`（新建，约 50 行）

**预计耗时:** 30 min | **规模:** S

---

#### Task T4: `chart_factory.py` 单元测试

**描述:** 测试 7 种图表类型生成正确类型对象 + 空数据异常。

**验收条件:**
- [ ] 7 种 `ChartType` 均生成对应 pyecharts 图表实例
- [ ] 空 `top20` → 抛出 `ChartFactoryError`
- [ ] 雷达图仅使用前 6 项数据

**验证:** `pytest tests/test_chart_factory.py -v`

**依赖:** B4

**涉及文件:**
- `tests/test_chart_factory.py`（新建，约 40 行）

**预计耗时:** 20 min | **规模:** S

---

#### Task T5: 集成手动测试

**描述:** 运行 `streamlit run app.py`，按 SC1-SC12 逐一验收。

**验收条件:**
- [ ] SC1-SC12 全部通过（参见 SPEC § Success Criteria）
- [ ] 测试记录填入课程报告 5.1 测试用例表

**验证:** 手动测试，记录截图

**依赖:** B10, B11, T1-T4

**涉及文件:**
- 无代码变更，生成测试截图

**预计耗时:** 45 min | **规模:** M

---

### Phase 5: REVIEW（评审）

#### Task R1: 代码质量审查

**描述:** 对照 SPEC § Boundaries 和 Code Style 自查代码。

**验收条件:**
- [ ] `app.py` 无业务逻辑实现函数（只有管线调用和 UI 组件）
- [ ] 所有公开函数有类型注解和 docstring
- [ ] 无硬编码文件路径
- [ ] 无 secrets/API key 写入代码
- [ ] 客户端未使用的 import 已移除

**验证:** 目视审查 `app.py` + 各 `modules/*.py`

**依赖:** T5

**涉及文件:**
- 全部（审查，酌情修改）

**预计耗时:** 30 min | **规模:** M

---

#### Task R2: UI/UX 审查

**描述:** 检查界面一致性、中文文案、交互反馈、边界状态展示。

**验收条件:**
- [ ] 所有按钮/提示/标签文字为中文
- [ ] 加载中有 spinner，成功有 toast
- [ ] 空状态有友好提示
- [ ] 错误状态不显示 traceback
- [ ] 各图表在 7 种类型下正常渲染

**验证:** 目视走查 + 截图

**依赖:** T5

**涉及文件:**
- `app.py`（文案调整）

**预计耗时:** 30 min | **规模:** S

---

### Phase 6: SHIP（交付）

#### Task S1: 最终化 `requirements.txt`

**描述:** 确认依赖版本锁定，确保 `pip install -r requirements.txt` 一键安装可用。

**验收条件:**
- [ ] 所有依赖版本与现有 `requirements.txt` 一致
- [ ] 无多余未使用依赖
- [ ] 新环境 `pip install -r requirements.txt` 后可直接 `streamlit run app.py`

**验证:** 在干净虚拟环境中安装测试

**依赖:** R2

**涉及文件:**
- `requirements.txt`

**预计耗时:** 15 min | **规模:** XS

---

#### Task S2: 撰写课程设计报告

**描述:** 将 SPEC.md、TASKS.md 内容填入报告模板对应章节，补充 BUILD/TEST/REVIEW/SHIP 各阶段的实际记录。

**验收条件:**
- [ ] §1 项目概述（更新为 v2 内容）
- [ ] §2 DEFINE（更新用户故事和功能清单）
- [ ] §3 PLAN（填入技术选型和任务拆分）
- [ ] §4 BUILD（粘贴核心代码片段 + 设计决策注释）
- [ ] §5 TEST（填入测试用例表 + Bug 记录）
- [ ] §6 REVIEW（填入审查结果）
- [ ] §7 SHIP（填入文件结构和运行方式）
- [ ] §8 改进前后对比（量化对比表 + 截图）
- [ ] §9 反思与总结

**验证:** 报告 Markdown 渲染检查

**依赖:** R2, S1

**涉及文件:**
- `课程设计报告模板_词频分析可视化系统.md`（填充）

**预计耗时:** 60 min | **规模:** L

---

#### Task S3: 项目成品打包

**描述:** 确认所有文件到位，截取 7 张图表截图放入 `images/` 目录，README 补充说明。

**验收条件:**
- [ ] `images/` 目录含 7 张截图
- [ ] 报告内图片链接有效
- [ ] GitHub 仓库可正常运行（如有推送）

**验证:** `streamlit run app.py` 最终验收

**依赖:** S2

**涉及文件:**
- `images/*.png`（新增）
- `README.md`（新建/更新）

**预计耗时:** 30 min | **规模:** S

---

## 简易甘特时间表

```
Phase     Task                    耗时      周次
─────────────────────────────────────────────────────
BUILD     B1  模块骨架            5 min    │
          B2  fetch_web           40 min   │ 第 1 天
          B3  text_clean_token    30 min   │ Foundation
          B4  chart_factory       30 min   │
          B5  history             40 min   │
          ── Checkpoint ──               │
          B6  app.py 重构         90 min   ├─ 第 2 天
          B7  多输入 + Session    60 min   │ Integration
          B8  历史记录面板        60 min   │
          B9  文本对比            45 min   │
          ── Checkpoint ──               │
          B10 UI 美化            45 min   ├─ 第 3 天
          B11 错误处理加固       30 min   │ Polish
          ── Checkpoint ──               │
─────────────────────────────────────────────────────
TEST      T1  text_clean_token    30 min   │
          T2  fetch_web           30 min   ├─ 第 4 天
          T3  history             30 min   │
          T4  chart_factory       20 min   │
          T5  集成手动测试        45 min   │
─────────────────────────────────────────────────────
REVIEW    R1  代码审查            30 min   ├─ 第 5 天
          R2  UI/UX 审查          30 min   │
─────────────────────────────────────────────────────
SHIP      S1  requirements.txt    15 min   │
          S2  课程报告            60 min   ├─ 第 5 天
          S3  成品打包            30 min   │
─────────────────────────────────────────────────────
                              合计 ≈ 12.5 h
```

---

## 适配课程报告 3.3 开发计划表

可直接填入报告：

| 阶段 | 任务 | 预计时长 | 依赖 | 交付物 |
|------|------|---------|------|--------|
| BUILD | 模块骨架 + fetch_web | 0.8 h | — | `modules/fetch_web.py` |
| BUILD | text_clean_token + chart_factory | 1.0 h | 模块骨架 | `modules/text_clean_token.py`, `chart_factory.py` |
| BUILD | history 模块 | 0.7 h | 模块骨架 | `modules/history.py` |
| BUILD | app.py 重构（使用模块） | 1.5 h | 全部模块 | 重构后的 `app.py` |
| BUILD | 多输入方式 + Session State | 1.0 h | app.py 重构 | Tab 切换 + 上传/粘贴 |
| BUILD | 历史记录面板 | 1.0 h | history 模块 | 持久化 + 回看/删除 |
| BUILD | 文本对比视图 | 0.8 h | 历史面板 | 双栏对比 + 叠加图表 |
| BUILD | UI 美化 + 错误处理 | 1.3 h | 全部功能 | 成品级界面 |
| TEST | 单元测试（4 个模块） | 1.8 h | 对应模块 | `tests/test_*.py` × 4 |
| TEST | 集成手动测试 | 0.8 h | 全部功能 | 测试截图 + 用例表 |
| REVIEW | 代码审查 + UI 审查 | 1.0 h | 测试通过 | 审查记录 |
| SHIP | requirements + 报告 + 打包 | 1.8 h | 审查通过 | 完整交付物 |

---

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Streamlit rerun 导致 session state 丢失 | 中 | B7 优先实现 session_state 框架，后续功能在此基础上追加 |
| pyecharts 图表在 streamlit-echarts 中渲染异常 | 中 | chart_factory 模块独立可测，B6 后立即验证全部图表 |
| jieba 分词精度不足（专有名词切碎） | 低 | 暂不引入自定义词典（SPEC Out of scope），保持现有清洗逻辑 |
| GBK 文件编码检测失败 | 低 | UTF-8→GBK 两级 fallback，均失败时给明确错误提示 |
| history.json 文件损坏 | 低 | 损坏时自动重建空数组，旧数据丢失但系统不崩溃 |

---

## 并行化机会

- **B2 / B3 / B4 / B5** 四个模块无相互依赖，可并行开发
- **T1 / T2 / T3 / T4** 对应模块的单元测试可并行编写
- **B10 和 B11** 可并行推进

---

## 修订历史

| 日期 | 变更 |
|------|------|
| 2024-06-23 | 初始版本，基于 SPEC v1.1 + API 接口设计 |
