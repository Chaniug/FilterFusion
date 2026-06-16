# FilterFusion 项目开发日志

> 涵盖架构决策、Bug 修复、性能优化全记录

---

## 项目概述

FilterFusion — 广告过滤规则聚合工具，从多源获取过滤规则，合并去重后分发。由 [Chaniug](https://github.com/Chaniug) 维护。

**技术决策速览**：
- Release Tag 格式 `YYYY.MM.DD`，标题 `FilterFusion Weekly · YYYY.MM.DD`
- Checksum 使用 ABP 标准 MD5 + Base64（24 字符）
- Python ≥ 3.10
- GitHub Actions 权限 `contents: write`

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

---

## 关键文件索引

| 文件 | 用途 |
|------|------|
| `.github/workflows/daily-update.yml` | 每日自动更新工作流 |
| `.github/workflows/weekly-release.yml` | 每周自动发布工作流 |
| `.github/workflows/static.yml` | GitHub Pages 部署 |
| `scripts/fetch_rules.py` | 规则抓取（并发下载 + 重试） |
| `scripts/merge_rules.py` | 规则合并去重（分类 + 去重 + 输出） |
| `config/sources.txt` | 规则源配置（名称 > URL） |
| `config/default.header` | 输出文件头部模板 |
| `rules/fetch_meta.json` | 抓取元数据 |
| `dist/adblock-*.txt` | 生成的规则文件 |
| `dist/summary.json` | 统计摘要 |
| `docs/merge_optimization_plan.md` | 本次优化方案详情 |
| `docs/PROJECT_LOG.md` | 本文件 — 开发日志 |
| `PROJECT_DOCS.md` | 完整项目文档 |
| `pyproject.toml` | 现代 Python 项目配置 |
