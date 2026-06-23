# FilterFusion 项目开发日志

> 涵盖架构决策、Bug 修复、性能优化全记录

---

## 项目概述

FilterFusion — 广告过滤规则聚合工具，从多源获取过滤规则，合并去重后分发。由 [Chaniug](https://github.com/Chaniug) 维护。

**技术决策速览**：
- Release Tag 格式 `YYYY.MM.DD`，标题 `FilterFusion Weekly · YYYY.MM.DD`
- Checksum 使用 ABP 标准 MD5 + Base64（24 字符）
- Python ≥ 3.14
- GitHub Actions 权限 `contents: write`


---

## 2026-06-23（CI/CD 重大升级与文档同步）

### 工作流版本升级
- **daily-update.yml**：
  - `actions/checkout@v6` → `v7.0.0`，消除 Node.js 20 弃用警告
  - `astral-sh/setup-uv@v5` → `v8.2.0`，消除 Node.js 20 弃用警告
  - Python 从 3.13 升级到 **3.14**（CI + `pyproject.toml` 同步更新）
  - AdBlock 和 DNS 抓取改为 **Shell 后台任务并行执行**，减少总运行时间
  - 提交前新增 **临时规则文件和 `__pycache__` 自动清理**，保持 `scripts/` 目录干净
  - 新增 `concurrency` 组控制，防止并发竞态
- **weekly-release.yml**：`actions/checkout@v6` → `v7.0.0`
- **static.yml**：`actions/checkout@v6` → `v7.0.0`

### 项目文档同步
- `PROJECT_DOCS.md` → v1.6，同步所有 CI/CD 细节（并行抓取、清理、新版 Action 版本）
- `README.md / README_EN.md / README_JP.md / README_KO.md` → Python 3.13 → 3.14 徽章与系统要求
- 修复英文/日文/韩文 README 中快速开始的错误目录命令

---

## 2026-06-19（文档修复）

### README 多语言文档修复
- **修复问题**：
  - `README.md`「应用场景」Mermaid 图表 `subgraph S4` 缺少 `end` 闭合标签，导致图表无法渲染
  - 中文/英文/日文/韩文四语言 README 目录（Table of Contents）均缺少 `系统要求` 和 `联系方式` 条目
  - 中文 README 目录顺序与文档实际结构不符（`联系方式`被错误插入到中间位置）
- **影响文件**：`README.md`、`README_EN.md`、`README_JP.md`、`README_KO.md`

---

## 2026-06-13（项目密集开发日）

### 项目文档与架构
- 生成完整项目文档 `PROJECT_DOCS.md`，涵盖架构、数据流、组件详解、使用方法、部署订阅、技术细节
- 为项目设计 4 套 AI 海报生成方案

### GitHub Release 优化
- Tag 格式从 `release-YYYY.MM.DD` 简化为 `YYYY.MM.DD`
- Release 标题从"每周规则集发布·稳定版"改为 `FilterFusion Weekly · YYYY.MM.DD`
- 添加 `permissions: contents: write`、`fetch-depth: 0`，利用 GitHub 内置验证使 Release 显示 Verified
- 手动触发 v2.0 重大更新 Release

### Checksum 修复
- 算法从 SHA-256（64 字符）改为 ABP 标准 MD5 + Base64（24 字符）
- 兼容 uBlock Origin、AdGuard 等所有主流拦截器
- 同步更新 `PROJECT_DOCS.md` 相关说明

### Header 模板优化
- 新增 `[Adblock Plus 2.0]` 首行声明
- 新增 `! TimeUpdated:` ISO 8601 字段
- `! Checksum:` 移至首行之后对齐 AdGuard 规范
- 规则统计行从硬编码改为模板占位符
- 修复模板末尾无换行导致与规则粘连的问题

### GitHub Actions 重大修复
- **daily-update.yml 终极方案**：放弃 rebase，改为「Actions 本地产出优先」策略 —— `git reset --soft origin/main` + `git checkout origin/main -- ':!dist'`，4 行命令零分支逻辑
- **weekly-release.yml**：创建 Tag 前添加 `git pull origin main`
- 升级 `actions/checkout@v4`→`@v6`、`actions/setup-python@v5`→`@v6`，消除 Node.js 20 弃用警告
- Python 版本从 3.10 升级到 3.12

### 全项目 Bug 审查（6 项）
1. `merge_rules.py`：修复 `##` 元素隐藏规则被误判为注释的严重 bug
2. `merge_rules.py`：`calculate_source_stats` 补上 `errors='replace'`
3. `fetch_rules.py`：超时从 15-25s 改为 35-65s，适配大型规则文件
4. `config/sources.json`：修复缩进
5. `weekly-release.yml`：LINE_COUNT 从 `wc -l` 改为 `grep -vcE` 仅统计实际规则行
6. `merge_rules.py`：新增 `element_hide` 分类，输出中独立成段

### Python 3.10+ 激进升级
1. 修复 `merge_rules.py` 缩进、删除 `fetch_rules.py` 未使用导入
2. 更新 `requirements.txt`：`requests>=2.31.0`
3. 为两个脚本添加完整类型注解
4. 创建 `pyproject.toml`（mypy/basedpyright/pytest/black/isort 配置）
5. 创建 `requirements-dev.txt`
6. 更新文档 Python 版本要求
7. basedpyright 验证：0 errors, 0 warnings, 0 notes

### 环境配置
- PowerShell 需禁用 `Microsoft.WinGet.CommandNotFound` 模块
- Windows 本地运行时需 `$env:PYTHONIOENCODING='utf-8'`

---

## 2026-06-14

### GitHub Actions 修复
- `python -m scripts.fetch_rules` 报错 → 创建 `scripts/__init__.py` 使 scripts 成为 Python 包
- `daily-update.yml`：移除 fetch 步骤的 `continue-on-error: true`，避免隐藏真实错误
- `generate_source_list` 中 `source['timestamp']` KeyError（disabled 源无此字段）→ 改用 `.get()` 安全访问

### 文档与配置同步
- 所有文档中 `sources.json` → `sources.txt`，添加 txt 格式配置指引
- `config/sources.txt`：Adguard Extra 从 CDN 改为 GitHub Raw 直连，减少跳转延迟
- `config/default.header`：Description 精简
- README 订阅地址：移除失效的 FastGit/GitHub Proxy，替换为 `gh.llkk.cc`

### Actions 版本升级
- `configure-pages@v6`、`upload-pages-artifact@v5`、`deploy-pages@v5`、`softprops/action-gh-release@v3`
- 移除 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` 环境变量
- `weekly-release.yml`：修复 tag 重复导致的 fatal 错误，打 tag 前先检查并删除旧 tag

---

## 2026-06-16（性能优化日）

### Phase 1 — merge_rules.py 核心性能
- 去重键 `f"{typ}:{rule}"` → `rule`（typ 前缀冗余）
- ASCII 快速路径跳过 99%+ 规则的 NFKC 调用
- 预编译正则 `_HTML_FILTER_RE` 替代 `any(k in rule for k in html_filter_keywords)` 多次子串扫描
- 去掉 `len(pattern) > 15` 兜底，降低误分类
- 删除 `_ = main_path.exists()` 死代码

### Phase 2 — GitHub Actions 效率
- `daily-update.yml` / `weekly-release.yml`：`fetch-depth: 0` → `1`
- `daily-update.yml`：添加 `concurrency` 控制防并发竞态

### Phase 3 — 脚本清理
- `groups['comment']` 不再存储无用注释
- 移除 `_ = f.write(content)` 多余赋值
- `fetch_rules.py`：清理不可达 `raise RuntimeError`

## 关键文件索引

---

## 2026-06-18（第二轮优化：Python 3.13 升级 + httpx 异步 + CI 加速 + 目录整理）

### Python 运行时升级
- `requires-python` 从 `>=3.10` 提升到 `>=3.13`
- 享受 CPython 3.13 specializing adaptive interpreter 带来的 ~5-10% 整体性能提升
- 应用现代语法：`datetime.UTC`、`StrEnum`、`type` 语句、`__slots__`、`from __future__ import annotations`
- mypy / basedpyright / black 工具链 target 版本同步升级到 3.13

### 网络层重构（fetch_rules.py）
- `requests.Session` + `ThreadPoolExecutor` → `httpx.AsyncClient` + `asyncio.gather()`
- 启用 HTTP/2 多路复用，3 个同在 raw.githubusercontent.com 的源共享单条 TLS 连接
- `FetchStatus(StrEnum)` 替代字符串字面量 `"success"` / `"failed"` / `"disabled"`
- `__slots__` 减少实例字典开销
- 修复所有 `open()` 的 `encoding='utf-8'`（Windows 本地运行隐患）
- 用 `Path.read_text` / `write_text` / `write_bytes` 替代裸 `open()`
- 入口改为 `asyncio.run(main())`

### 合并热路径优化（merge_rules.py）
- `special_keywords` 列表提升为类级 `_SPECIAL_RE` 预编译正则（单次 C 层扫描替代 8 次 `any(in)`）
- 正则字符检测提升为类级 `_REGEX_CHAR_RE` 预编译正则（单次字符类扫描替代 14 次 `any(in)`）
- `RuleType(StrEnum)` 枚举替代 groups 字典的字符串键
- header 模板 11 次链式 `.replace()` → 单次 `format_map()` + `_SafeDict`（`__missing__` 保持 `{CHECKSUM}` 占位符）
- 消除重复 `datetime.now(timezone.utc)` 调用（2 次合并为 1 次 `datetime.now(UTC)`）
- `__slots__` 减少实例内存
- 修复 3 处 `open()` 的 `encoding='utf-8'`

### GitHub Actions CI 加速
- `daily-update.yml` / `weekly-release.yml`：Python 3.12 → 3.13
- `pip install` → `uv pip install --system`（配合 `astral-sh/setup-uv@v6` + `enable-cache`，依赖安装 10-100 倍加速）
- `daily-update.yml`：抓取 + 合并合并为单个 step；26 行 bash 清理脚本简化为 `find dist -name "adblock-[0-9]*.txt" -mtime +2 -delete`
- `weekly-release.yml`：添加 `concurrency` 控制（防并发竞态）
- `static.yml`：添加 `paths` 过滤（`dist/**` + 工作流自身），避免脚本/文档/配置变更触发无意义 Pages 重新部署

### 依赖变更
- `requirements.txt`：`requests>=2.31.0` → `httpx[http2]>=0.27.0`
- `requirements-dev.txt`：移除 `types-requests`（httpx 内置类型桩），升级开发依赖最低版本
- `pyproject.toml`：`dependencies` 同步更新

### 输出不变性
- `dist/adblock-main.txt`、`dist/adblock-YYYYMMDD.txt`、`config/summary.json` 位置与格式完全不变
- checksum 算法（ABP 标准 MD5 + Base64）、header 模板占位符行为保持一致

### DNS 规则支持
- 新增 `config/dns_sources.txt`（DNS 规则源配置）、`config/dns.header`（DNS 头部模板）
- 新增 `scripts/fetch_dns_rules.py`（异步抓取 DNS 规则源）、`scripts/merge_dns_rules.py`（DNS 规则去重合并）
- DNS 规则合并简化（无复杂分类逻辑，仅例外规则 + 普通规则去重）
- CI `daily-update.yml` 新增 DNS 抓取/合并/校验步骤
- 输出：`dist/dns-blocklist.txt`（主文件）、`dist/dns-blocklist-YYYYMMDD.txt`（日期归档）、`config/dns_summary.json`

### 历史归档策略调整
- `dist/` 历史文件保留从 **3 天缩减到 1 天**（`-mtime +2` → `-mtime +0`）
- 原因：DNS 规则引入后历史文件数量翻倍，保持 dist 目录清爽
- 用户需回溯更早版本可通过 git 历史获取

### 目录整理
- **动机**：`dist/` 下混入 `summary.json` 和 `dns_summary.json` 体感不好，`rules/` 目录名不副实（里面只存抓取元数据而非规则）
- **删除 `rules/` 目录**：`fetch_meta.json` 和 `dns_fetch_meta.json` 移入 `scripts/`，它们是脚本的运行时缓存
- **净化 `dist/`**：`summary.json` 和 `dns_summary.json` 移入 `config/`，`dist/` 只保留纯规则 `.txt` 文件
- **根目录零散文件归位**：`_cdnauth.txt` 移入 `config/`，`PROJECT_DOCS.md` 移入 `docs/`
- **同步更新**：4 个脚本的 `rules_dir` → `scripts`、summary JSON 路径 → `config/`；`.gitignore` 移除 `rules/` 忽略规则；`daily-update.yml` 的 git checkout/add 覆盖 `config` 和 `scripts`；`PROJECT_DOCS.md` 全量路径更新
- **最终架构**：5 个文件夹（`assets/` `config/` `dist/` `docs/` `scripts/`），净减少 1 个

| 文件 | 用途 |
|------|------|
| `.github/workflows/daily-update.yml` | 每日自动更新工作流 |
| `.github/workflows/weekly-release.yml` | 每周自动发布工作流 |
| `.github/workflows/static.yml` | GitHub Pages 部署 |
| `scripts/fetch_rules.py` | 规则抓取（并发下载 + 重试） |
| `scripts/merge_rules.py` | 规则合并去重（分类 + 去重 + 输出） |
| `config/sources.txt` | 规则源配置（名称 > URL） |
| `config/default.header` | 输出文件头部模板 |
| `scripts/fetch_meta.json` | 抓取元数据 |
| `dist/adblock-*.txt` | 生成的规则文件 |
| `config/summary.json` | 统计摘要 |
| `docs/merge_optimization_plan.md` | 本次优化方案详情 |
| `docs/PROJECT_LOG.md` | 本文件 — 开发日志 |
| `docs/PROJECT_DOCS.md` | 完整项目文档 |
| `pyproject.toml` | 现代 Python 项目配置 |

---

## 2026-06-22（README 全面可视化优化）

### 数据呈现升级（4 语种同步）
- **规则分类体系表** — 新增 7 级 ABP 分类表格，附 emoji 颜色标记，位于"工作原理"末尾
- **输出文件一览表** — Q4 从纯文本代码块改为表格，新增 `dist/summary.json` 条目
- **兼容工具速览表** — 新增工具 × 规则类型的二维表格，位于"导入工具"下方
- **规则订阅地址独立代码块** — 每条链接独立 `text` 代码块，GitHub 自动渲染复制按钮，方便用户一键复制

### 布局与格式优化
- **系统要求表格化** — 无序列表 + 2 个代码块 → 压缩为 1 张表格 + 1 行命令
- **快速开始统一步骤** — 步骤编号统一（1/2/3/4），AdBlock/DNS 命令合并为速查表
- **修复目录锚点链接** — 移除 `##` 标题中的 emoji，确保 VS Code 预览和 GitHub 均能正确跳转

### 影响文件
- `README.md`、`README_EN.md`、`README_JP.md`、`README_KO.md`（4 语种全量同步）
