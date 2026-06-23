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

## 2026-06-23（配置 YAML 迁移 + 自定义组合规则）

### 配置格式迁移：txt → YAML

- `config/sources.txt` → `config/sources.yaml`：`[M|P|B]|名称|URL` 改为 YAML 结构（`id` / `category` / `name` / `url`）
- `config/dns_sources.txt` → `config/dns_sources.yaml`：`名称|URL` 改为 YAML 结构（`name` / `url`）
- 新增 `pyyaml>=6.0` 依赖（`requirements.txt` + `pyproject.toml` 同步）
- 动机：GitHub 网页编辑 YAML 有语法高亮，缩进结构清晰，手机端编辑友好；key:value 自文档化，扩展字段只需加 key

### 自定义组合规则（custom_rules）

- `sources.yaml` 新增 `custom_rules` 段：按 ID 引用已抓取的源，合并去重后输出到 `dist/`
- 每个 AdBlock 源分配短 ID（m1/m2/m3/b1/b2/p1），被组合规则按 ID 引用
- `merge_rules.py`：提取 `_do_merge` 通用方法（复用分类、去重、校验和、头部模板逻辑）；新增 `merge_custom(output, source_ids)` 方法
- `merge_all.py`：标准 3 合并后，从 `fetch_meta.json` 读取 `custom_rules`，循环调用 `merge_custom`
- `base_fetcher.py`：`__slots__` 新增 `custom_rules`；`_build_success`/`_build_failure`/`_build_disabled` 及共享下载结果传播 `id` 字段；元数据输出 `custom_rules`
- 零额外网络开销：组合规则引用的源已被主流程抓取，合并阶段仅读本地文件

### 抓取层适配

- `fetch_rules.py`：`load_sources()` 重写为 `yaml.safe_load` 解析，提取 `sources` + `custom_rules`，ID 冲突检测
- `fetch_dns_rules.py`：`load_sources()` 重写为 `yaml.safe_load` 解析 `dns_sources.yaml`
- B（both）源两条记录共享同一 ID，组合规则按 ID 引用时按 `file` 去重避免重复处理

### 工作流适配

- `daily-update.yaml`：校验步骤保留 3 个标准文件硬性校验 + 列举自定义文件
- `weekly-release.yml`：打包改为 `zip *.txt` 通配；统计步骤动态统计 `dist/*.txt` 规则数

### 文档同步

- `README.md` / `README_EN.md`：配置示例改为 YAML + custom_rules 说明、Mermaid 数据流图新增组合规则分支、Q2 FAQ 更新
- `PROJECT_DOCS.md`：4.1 节配置格式全量重写、目录结构更新、数据流图更新、4.3 节新增 merge_custom 说明、输出产物新增自定义规则章节、维护指南新增组合规则配置说明

### 核心规则迁移到 custom_rules 驱动

- `adblock-mo.txt` / `adblock-pc.txt` 从硬编码 `merge()` 迁移到 `custom_rules` 配置驱动，文件名和订阅链接保持不变
- `sources.yaml` 的 `custom_rules` 新增可选 `description` 字段，核心规则使用原有描述文本（`Ad blocking rules (Mobile/PC)`）
- `fetch_rules.py`：解析 `custom_rules` 时读取 `description` 字段
- `merge_rules.py`：`merge_custom` 方法新增 `description` 参数，优先使用配置描述，未提供时自动生成
- `merge_all.py`：移除硬编码的 `RuleMerger(category="mobile").merge()` 和 `RuleMerger(category="pc").merge()` 调用，AdBlock 规则全部通过 `custom_rules` 统一驱动；DNS 管道保持独立
- 动机：所有 AdBlock 产出文件统一由配置驱动，新增/修改规则只需编辑 `sources.yaml`，无需改代码

---

## 2026-06-23（性能优化 + 配置重构 + 日志精简）

### GitHub Actions 性能优化

#### 1. 统一合并入口（进程合并）
- 新建 `scripts/merge_all.py`：单进程顺序执行 mobile/pc/DNS 3 个合并任务
- `daily-update.yaml`：3 个合并 step → 1 个 `uv run --no-project python -m scripts.merge_all`
- 减少 2 次 Python 解释器启动开销（约 0.6-1s），对齐已有的 `fetch_all.py` 单进程模式

#### 2. 抽取共享 Fetch 基类
- 新建 `scripts/base_fetcher.py`，定义 `BaseFetcher` 基类
- 共享 `FetchStatus` 枚举、`fetch_single_rule`、`fetch_all_rules`、`_build_success`/`_build_failure`/`_build_disabled`
- `fetch_rules.py` 261→90 行，`fetch_dns_rules.py` 244→80 行
- 子类仅实现 `load_sources()`

#### 3. 修复 weekly-release 规则数重复统计 bug
- `cat dist/adblock-main.txt dist/adblock-main-*.txt ...` 通配符同时匹配规范文件和日期归档，规则数翻倍
- 修复：统计只用规范文件

#### 4. 其他优化
- `merge_dns_rules.py`：移除 `final_rule_count` 死代码，8 次链式 `.replace()` → 单次 `format_map()`
- `pyproject.toml`：mypy/basedpyright `python_version` 3.10 → 3.14

### dist 目录简化：移除日期快照

- 移除所有 `adblock-*-YYYYMMDD.txt` 和 `dns-blocklist-YYYYMMDD.txt` 日期快照文件
- `merge_rules.py` / `merge_dns_rules.py`：直接写入规范文件名，不再生成快照+copyfile
- `daily-update.yaml`：删除"清理旧的规则文件"整个 step
- `weekly-release.yml`：zip 打包和统计只用 3 个规范文件
- dist 最终只保留：`adblock-mo.txt`、`adblock-pc.txt`、`dns-blocklist.txt`

### 配置格式重构

#### 1. 分隔符 `>` → `|`
- `config/sources.txt`：`M|名称|URL` / `P|名称|URL` / `B|名称|URL`
- `config/dns_sources.txt`：`名称|URL`
- 理由：`>` 一符两用语义混淆，`|` 语义清晰

#### 2. 新增 B 前缀（两端共用）
- `B` 展开为 mobile + pc 两条 source 记录（URL 相同）
- `base_fetcher.py` 的 `fetch_all_rules()` 按 URL 去重：同 URL 只下载一次，结果共享给所有同 URL 的 source 记录
- AdGuard Chinese 和 Chaniug AdSuper 改用 B 前缀，各省一次下载

#### 3. adblock-main.txt → adblock-mo.txt
- 移动端文件名从 `adblock-main.txt` 改为 `adblock-mo.txt`（mo = Mobile，更直观）
- 同步更新 `merge_rules.py`、`daily-update.yaml`、`weekly-release.yml`、README

### PC 端规则源扩充

PC 端从 1 个源扩充到 4 个，与移动端对齐：
- `AdGuard Base`（替代原 Android 优化版）
- `AdGuard Chinese`（B 共用）
- `Chaniug AdSuper`（B 共用）
- `EasyList`（新增）
- 全部使用 `raw.githubusercontent.com` 同域，HTTP/2 多路复用
- 另加 3 条 AdGuard optimized 版本作为禁用注释源

### 日志精简

精简所有脚本的 CI 日志输出，减少约 60-70% 日志量：
- 去掉所有 `=`*50 分隔线横幅
- 去掉路径调试信息（项目根目录、规则目录、元数据文件、配置文件路径）
- 去掉"步骤1/2/3..."逐步标签
- 去掉逐源文件处理路径和规则数（最终摘要有汇总）
- 合并结果摘要压缩为一行：`✅ AdBlock [mobile] 合并完成: 31367 → 31340 条 (去重 27, 1.23s) → dist/adblock-mo.txt`
- 保留：阶段标识、源数量、抓取成功/失败、最终摘要、所有错误和警告

### 文档同步
- `README.md` / `README_EN.md`：订阅地址改为代码块分组范式（每块 3 行 CDN + blockquote 说明）、配置示例改为 `|` 格式 + B 前缀、Mermaid 图和 Q4 表格同步、删除过时 summary.json 引用、补充 PC 端订阅地址
- `PROJECT_DOCS.md` → v1.8，全量同步配置格式、输出产物、订阅地址、目录结构

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
- `README.md / README_EN.md` → Python 3.13 → 3.14 徽章与系统要求
- 修复英文 README 中快速开始的错误目录命令（精简为仅维护中/英文）

---

## 2026-06-23（移动端/电脑端规则分离）

### 规则类别分离
- **`config/sources.txt`** 格式升级：新增 `M>`（移动端） / `P>`（电脑端）前缀，每行格式为 `[M|P]>名称 > URL`
- **`scripts/fetch_rules.py`**：`load_sources()` 解析 M/P 前缀，将 `category` 写入 `fetch_meta.json`
- **`scripts/merge_rules.py`**：新增 `--category mobile|pc` CLI 参数，按类别过滤源，分别输出到不同的文件
- **`config/default.header`**：`Description` 行改为 `{DESCRIPTION}` 占位符，由合并脚本动态填充
- **Header `SOURCE_LIST`** 修复：只显示匹配类别的源，不再混入不需要的源

### 输出产物变更
- `dist/adblock-main.txt` → **移动端规则**（M 类源）
- `dist/adblock-pc.txt` → **电脑端规则**（P 类源）
- 新增 P 类源：`Adguard PC`（AdGuard 基础过滤规则）
- 禁用源：`uniartisan`（标注 `#` 注释）

### 新增规则源
- `P>Adguard PC` 启用（含 EasyList+EasyPrivacy 等桌面端规则，~48,000 条有效规则）

---

## 2026-06-23（统一抓取入口与项目清理）

### 统一抓取入口
- **`scripts/fetch_all.py`**（新建）：统一入口，用 `asyncio.gather` 在单进程单事件循环中同时执行 AdBlock + DNS 抓取
- **`daily-update.yaml`**：抓取步骤从两次 `uv run`（Shell 后台任务）简化为单行 `python -m scripts.fetch_all`
- 消除重复 Python 进程启动开销和独立的 httpx 连接池

### 元数据路径迁移
- `fetch_meta.json` 和 `dns_fetch_meta.json` 写入系统临时目录（`/tmp/filterfusion/`），运行后自动销毁
- 取消 Git 追踪，加入 `.gitignore`
- `summary.json` 和 `dns_summary.json` 改为控制台输出，不再生成文件

### 项目清理
- `.codebuddy/` 取消 Git 追踪并加入 `.gitignore`
- 删除 `requirements-dev.txt`、`docs/plans/`、`docs/merge_optimization_plan.md`
- `config/` 目录中移出 `summary.json` 和 `dns_summary.json`

### Archives 部署优化
- `static.yml`：`static_site_generator: none` → `.nojekyll` 文件跳过 Jekyll 构建；`cancel-in-progress: true` 避免排队

---

## 2026-06-19（文档修复）

### README 多语言文档修复
- **修复问题**：
  - `README.md`「应用场景」Mermaid 图表 `subgraph S4` 缺少 `end` 闭合标签，导致图表无法渲染
  - 中文/英文 README 目录（Table of Contents）均缺少 `系统要求` 和 `联系方式` 条目
  - 中文 README 目录顺序与文档实际结构不符（`联系方式`被错误插入到中间位置）
- **影响文件**：`README.md`、`README_EN.md`

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
- `README.md`、`README_EN.md`（2 语种全量同步；日文/韩文后续已移除，精简为只维护中/英文）

---

## 2026-06-23（sources.yaml 易读性优化）

### 字段顺序调整（方案 A）
- `config/sources.yaml` 字段顺序改为 `name → category → url → id`（name 优先便于阅读，id 放最后降低视觉优先级）
- 顶部字段说明详细解释了 id 的用途："被 custom_rules 按 ID 引用来组合产出文件"

### category 缩写（方案 B）
- `category` 值改为缩写：`mo`（手机端）/ `pc`（电脑端）/ `bo`（两端共用），减少手写字数
- `scripts/fetch_rules.py` 新增 `CATEGORY_MAP` 映射表常量，将缩写映射为内部全称（`mo→mobile` / `pc→pc` / `bo→both`），同时兼容旧全称写法，向后兼容无破坏
- 内部 metadata（fetch_meta.json）仍存全称，`merge_rules.py` / `merge_all.py` / `base_fetcher.py` 零改动

### 顶部注释优化
- 新增"复制即用"模板注释块（新增源 + 新增组合规则各一段），普通人只需改 2-3 处即可
- 注明"YAML 对大小写敏感，所有值建议用小写"
- 详细说明 id 是什么、为什么要填

### 影响文件
- `config/sources.yaml`（主改动）
- `scripts/fetch_rules.py`（新增 CATEGORY_MAP + 更新 docstring）
- `docs/PROJECT_DOCS.md`、`README.md`、`README_EN.md`（同步示例和说明）

---

## 2026-06-23（sources.yaml 给源加说明注释）

### 源说明注释约定
- `config/sources.yaml` 顶部字段说明区新增【给源写说明？】约定段：告知可在源上方加 `#` 注释说明用途，脚本会忽略
- 给 6 个源各加一行说明注释：
  - AdGuard Mobile (m1)：AdGuard 官方移动端过滤规则（默认手机端拦截）
  - Adguard Extra (m2)：AdGuard 实验性补充规则（清理弹窗、额外广告元素）
  - Adguard Mobilestandard (m3)：AdGuard 移动端优化版（针对移动网络优化，规则更精简）
  - AdGuard Chinese (b1)：AdGuard 中文广告过滤规则（手机端 + 电脑端共用）
  - Chaniug AdSuper (b2)：作者自维护的补充规则集（两端的额外拦截补充）
  - AdGuard Base (p1)：AdGuard 桌面端基础过滤规则（默认电脑端拦截）
- 纯注释改动，脚本零影响，无破坏性变更

### 影响文件
- `config/sources.yaml`（仅注释）


