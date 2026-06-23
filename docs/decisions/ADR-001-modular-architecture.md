# ADR-001: 单文件单体 → 多文件模块化架构

## Status
Accepted

## Date
2026-06-23

---

## Context

项目起初为快速原型：一个 `app.py`（262 行）承载了所有逻辑——网页抓取、文本清洗、jieba 分词、Counter 统计、7 种 pyecharts 图表构造、Streamlit UI 编排。原型阶段可行，但现在面临 v2 升级：

1. **新增 3 种输入方式**（上传 TXT/MD、粘贴文本、保留 URL）
2. **新增历史记录持久化**（JSON 文件读写、50 条 FIFO）
3. **新增文本对比功能**（双栏 Top20 + 叠加柱状图）
4. **UI 重构**（Tabs、卡片式历史、Session State 管理）

如果全部写入 `app.py`，预估文件将膨胀至 **500–800 行**，函数间耦合加剧，任何修改都需在 `main()` 巨型函数内部定位代码。

### 当前 `app.py` 的结构性缺陷

| 问题 | 表现 | 后果 |
|------|------|------|
| **单函数垄断** | `main()` 包含全部逻辑（约 200 行）| 无法独立测试任何模块 |
| **关注点混杂** | 正则清洗、jieba 调用、pyecharts 图表、Streamlit 布局混在一个文件 | 改图表参数可能改错清洗逻辑 |
| **代码重复** | 7 种图表的 if-elif 分支共享相同模式但各自复制 | 新增第 8 种图表需复制整个分支 |
| **无异常分层** | `except Exception as e` 一把抓所有错误 | URL 超时、编码错误、空文本全显示同一个模糊提示 |
| **不可测试** | 所有逻辑与 Streamlit UI 耦合，无法脱离浏览器做单元测试 | 回归全靠手动 |
| **隐式耦合** | 清洗正则、分词参数、图表布局参数散落在 `main()` 各段 | 改参数需在 200 行中搜寻 |

---

## Decision

将 `app.py` 拆分为 **4 个纯 Python 模块** + **1 个 UI 编排入口**：

```
text-analysis-app/
├── app.py                    # 仅 UI 编排（Streamlit 组件调用）
├── modules/
│   ├── fetch_web.py          # 文本获取（URL 抓取 + 文件上传编码检测）
│   ├── text_clean_token.py   # 清洗 → 分词 → 词频统计管线
│   ├── chart_factory.py      # pyecharts 图表工厂（ChartType 枚举 → 图表对象）
│   └── history.py            # JSON 历史记录持久化
└── data/
    └── history.json           # 运行时数据
```

### 核心约束

- **只有 `app.py` 可以导入 `streamlit`** — 4 个模块是纯 Python，不感知 UI 框架
- **模块之间无横向依赖** — `fetch_web` 不调 `chart_factory`，依赖仅通过 `app.py` 编排
- **每个模块有独立异常体系** — `FetchError` / `TextProcessError` / `ChartFactoryError`，含可直接展示给用户的 `user_message`

---

## Alternatives Considered

### A: 保持单文件，仅在 `main()` 内拆函数

```python
# app.py 内部
def _fetch_url(url): ...
def _clean_text(raw): ...
def _segment(text): ...
def _make_chart(chart_type, data): ...
def main(): ...
```

| 维度 | 评估 |
|------|------|
| Pros | 零结构变更，改造成本最低 |
| Cons | 所有函数仍在同一文件，无法独立 import；无法用 pytest 脱离 Streamlit 测试；文件仍持续膨胀 |
| **Rejected:** 表面拆分了函数，实质耦合未解——改一个函数仍需理解整个文件的上下文。单文件 500+ 行在代码审查和调试中不可持续。 |

### B: 引入 FastAPI 后端 + Streamlit 前端分离

```python
# backend/app.py   → FastAPI REST API
# frontend/app.py  → Streamlit，通过 HTTP 调用后端
```

| 维度 | 评估 |
|------|------|
| Pros | 前后端彻底解耦；API 可复用；生产级架构 |
| Cons | 新增 FastAPI + uvicorn + httpx 依赖；本地启动从前端一键变成双进程；课程作业复杂度远超需求 |
| **Rejected:** 课程作业定位为本地单机工具，多进程架构是过度设计。用户不需要 REST API，不需要多用户并发，不需要部署。 |

### C: 按功能拆为 3 个 Streamlit pages

```python
# pages/1_输入.py
# pages/2_分析.py
# pages/3_历史.py
```

| 维度 | 评估 |
|------|------|
| Pros | Streamlit 原生多页支持；天然路由隔离 |
| Cons | 页面间数据共享依赖 `st.session_state` 或文件，用户需在页面间跳转；分析+图表+历史在同一页面内更自然 |
| **Rejected:** 分词→图表→保存这条流程在同一个页面内更流畅。多页路由反而增加了用户操作步骤，与"输入即分析"的体验目标冲突。 |

---

## Consequences

### 收益

| 维度 | 改进前（v1） | 改进后（v2） |
|------|-------------|-------------|
| **可测试性** | 0 个单元测试（全部耦合 UI）| 4 个模块均可脱离 Streamlit 单独 pytest |
| **代码定位** | 在 262 行中搜索函数片段 | 每模块 60–100 行，职责明确 |
| **图表扩展** | 新增图表 = 复制 if-elif 分支 + 40 行 | 新增 `ChartType` 枚举值 + 1 个 builder 函数 |
| **异常处理** | `except Exception` 一把抓 | 6+3+1 个语义化异常子类，按类型展示不同用户提示 |
| **文件耦合** | 全部在 `app.py` | `app.py` 仅编排，业务逻辑全在 modules |
| **复用性** | 无法被其他项目 import | `fetch_web`、`text_clean_token` 可单独被其他脚本引用 |

### 代价

| 代价 | 缓解 |
|------|------|
| 文件数从 1 增至 7+ | 命名遵循 `模块_动词` 约定，目录结构在 SPEC § Project Structure 和 README 中标注 |
| 模块间数据传递依赖 `AnalysisResult` 数据类 | 这是显式契约，比隐式 dict 传递更可维护 |
| 新人需理解模块依赖图 | `app.py` 顶部 import 即为依赖清单，文档化在 SPEC § Architecture |
| Streamlit 热重载覆盖 `modules/` | Streamlit 默认 `--server.runOnSave` 监听全部源码变更，无额外配置 |

### 中立事实

- 总代码行数增加约 1.3–1.5×（模块间的 import / 类型注解 / docstring 属于显式化成本）
- 运行时性能无差异（Python import 缓存，函数调用开销可忽略）
- `app.py` 中不再有"50 行业务逻辑函数"（SPEC Boundaries 约束）

---

## 设计原则对应

本次拆分遵循以下工程原则：

1. **单一职责（SRP）** — 每个模块只有一个变更理由：
   - `fetch_web` 变 = 输入来源变
   - `text_clean_token` 变 = 清洗/分词策略变
   - `chart_factory` 变 = 图表类型/样式变
   - `history` 变 = 存储格式/策略变

2. **依赖倒置** — 模块不依赖 Streamlit，依赖抽象的数据类（`AnalysisResult`、`ChartType` 枚举）

3. **开闭原则** — 新增图表类型 = 新增 `ChartType` 枚举值 + `create_chart()` 内的 case 分支，不修改已有图表逻辑

4. **边界验证** — 异常在模块边界定义（`FetchError` 子类），UI 层 `app.py` 只负责 `try/except` + `st.error(user_message)`

---

## 相关文档

- [SPEC.md](../../SPEC.md) — 系统规格 v1.1
- [TASKS.md](../../TASKS.md) — 实现任务拆分
- API 接口设计 — `fetch_web` / `text_clean_token` / `chart_factory` / `ui_layout` 4 模块接口契约

---

## 修订历史

| 日期 | 变更 |
|------|------|
| 2026-06-23 | 初始版本，记录 v1 单文件 → v2 模块化架构决策 |
