---
name: dns-filter-rules-support
overview: 为 FilterFusion 项目添加 DNS 过滤规则的自动合并功能，包括新增 DNS 规则源配置、抓取脚本、合并脚本，以及更新 GitHub Actions 工作流和文档
todos:
  - id: create-dns-config
    content: 创建 DNS 规则配置文件（config/dns_sources.txt、config/dns.header）
    status: completed
  - id: create-fetch-dns-script
    content: 创建 DNS 规则抓取脚本（scripts/fetch_dns_rules.py，复用异步抓取逻辑）
    status: completed
    dependencies:
      - create-dns-config
  - id: create-merge-dns-script
    content: 创建 DNS 规则合并脚本（scripts/merge_dns_rules.py，简化去重合并）
    status: completed
    dependencies:
      - create-fetch-dns-script
  - id: update-ci-workflow
    content: 更新 CI 工作流（.github/workflows/daily-update.yml，添加 DNS 规则处理步骤）
    status: completed
    dependencies:
      - create-merge-dns-script
  - id: update-documentation
    content: 更新项目文档（README.md、README_EN.md、PROJECT_DOCS.md，添加 DNS 规则说明）
    status: completed
    dependencies:
      - update-ci-workflow
  - id: test-dns-rules
    content: 测试 DNS 规则抓取和合并功能（本地运行验证）
    status: completed
    dependencies:
      - update-documentation
---

## 用户需求

为 FilterFusion 项目添加 DNS 过滤规则的自动合并功能，实现双规则支持（AdBlock 规则 + DNS 过滤规则）。

## 产品概述

FilterFusion 目前仅支持 AdBlock 过滤规则的合并。本次升级将添加 DNS 过滤规则的自动抓取、合并和去重功能，使项目同时支持浏览器过滤（AdBlock 规则）和网络级过滤（DNS 规则），扩大适用范围。

## 核心功能

1. **新增 DNS 规则源配置**：创建独立的 `config/dns_sources.txt` 配置文件，用于定义 DNS 拦截规则的源
2. **DNS 规则抓取**：复用现有异步抓取逻辑，创建 `scripts/fetch_dns_rules.py` 脚本
3. **DNS 规则合并**：创建 `scripts/merge_dns_rules.py` 脚本，处理 DNS 规则的合并和去重（比 AdBlock 规则合并简单）
4. **输出 DNS 规则文件**：生成 `dist/dns-blocklist.txt` 和按日期归档的文件
5. **更新 CI 工作流**：在 `.github/workflows/daily-update.yml` 中添加 DNS 规则的抓取和合并步骤
6. **更新项目文档**：在 README.md、README_EN.md、PROJECT_DOCS.md 中添加 DNS 规则说明

## 技术栈选择

- **编程语言**: Python 3.14（与项目现有环境一致）
- **HTTP 客户端**: httpx[http2]>=0.27.0（复用现有依赖）
- **异步框架**: asyncio（复用现有逻辑）
- **文件处理**: pathlib.Path（复用现有模式）

## 实现方法

### 总体策略

采用**模块化扩展**策略，复用现有 AdBlock 规则处理的异步抓取逻辑，新增独立的 DNS 规则处理流程。DNS 规则合并比 AdBlock 规则合并**简单很多**，因为：

- DNS 规则是 AdBlock 规则的子集，不支持元素隐藏、HTML 过滤等浏览器专属语法
- 不需要复杂的规则分类逻辑，主要是域名去重
- 不需要 ABP 校验和计算

### 关键技术方案

1. **配置分离**：创建 `config/dns_sources.txt` 作为 DNS 规则源配置，格式与 `sources.txt` 保持一致（名称 > URL）
2. **脚本复用**：

- `fetch_dns_rules.py` 复用 `fetch_rules.py` 的异步抓取逻辑（httpx.AsyncClient + asyncio.gather）
- 修改文件路径：规则保存到 `rules/dns_` 前缀的文件，元数据保存到 `rules/dns_fetch_meta.json`

3. **简化合并**：

- `merge_dns_rules.py` 实现简化的合并逻辑（不需要 RuleType 分类）
- DNS 规则去重：直接对规则文本去重（不需要 Unicode NFKC 规范化，因为 DNS 规则主要是 ASCII）
- 输出格式：按例外规则、普通规则分组即可

4. **独立头部模板**：创建 `config/dns.header`，不含 `[Adblock Plus 2.0]` 声明和 `{CHECKSUM}` 占位符

### 性能考虑

- **抓取性能**：复用 HTTP/2 多路复用，DNS 规则源通常与 AdBlock 规则源不同域，并发下载无冲突
- **合并性能**：DNS 规则去重比 AdBlock 规则简单，预期处理时间 < 0.1 秒
- **存储开销**：新增 `rules/dns_*.txt` 文件，预计 < 5MB

### 避免技术债务

- 保持与现有项目架构一致：脚本放在 `scripts/` 目录，配置放在 `config/` 目录
- 复用现有代码模式：异步抓取、元数据保存、错误处理等
- 不修改现有脚本，避免引入回归问题

## 实施要点

### 性能优化

- DNS 规则去重使用集合（set）数据结构，O(1) 查找
- 规则文件使用流式读取，避免大文件内存溢出
- 复用 httpx.AsyncClient 连接池

### 日志记录

- 复用现有 print 日志模式（项目未使用 logging 模块）
- 关键信息：抓取成功/失败、规则数量、去重数量

### 影响范围控制

- 不影响现有 AdBlock 规则处理流程
- 新增文件独立，不修改现有文件的核心逻辑
- CI 工作流新增步骤，但并行执行，不影响现有步骤

## 架构设计

### 系统架构

采用**双流水线架构**，AdBlock 规则和 DNS 规则独立处理，共享部分基础设施（httpx 客户端、文件路径工具等）。

```
┌────────────────────┐      ┌────────────────────┐
│ config/sources.txt │      │ config/dns_sources │
│ (AdBlock 规则源)   │      │        .txt        │
└──────────┬─────────┘      └────────┬───────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐      ┌────────────────────┐
│ scripts/           │      │ scripts/           │
│  fetch_rules.py    │      │  fetch_dns_        │
│  (AdBlock 抓取)    │      │  rules.py          │
└──────────┬─────────┘      └────────┬───────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐      ┌────────────────────┐
│ rules/*.txt        │      │ rules/dns_*.txt    │
│ rules/fetch_       │      │ rules/dns_fetch_   │
│  meta.json         │      │  meta.json          │
└──────────┬─────────┘      └────────┬───────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐      ┌────────────────────┐
│ scripts/           │      │ scripts/           │
│  merge_rules.py    │      │  merge_dns_        │
│  (AdBlock 合并)    │      │  rules.py          │
└──────────┬─────────┘      └────────┬───────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐      ┌────────────────────┐
│ dist/adblock-      │      │ dist/dns-           │
│  main.txt          │      │  blocklist.txt      │
│  (AdBlock 规则)    │      │  (DNS 规则)        │
└────────────────────┘      └────────────────────┘
```

### 模块划分

1. **配置模块**：

- `config/sources.txt` — AdBlock 规则源配置（已有）
- `config/dns_sources.txt` [NEW] — DNS 规则源配置
- `config/default.header` — AdBlock 规则头部模板（已有）
- `config/dns.header` [NEW] — DNS 规则头部模板

2. **抓取模块**：

- `scripts/fetch_rules.py` — AdBlock 规则抓取（已有）
- `scripts/fetch_dns_rules.py` [NEW] — DNS 规则抓取

3. **合并模块**：

- `scripts/merge_rules.py` — AdBlock 规则合并（已有）
- `scripts/merge_dns_rules.py` [NEW] — DNS 规则合并

4. **输出模块**：

- `dist/adblock-main.txt` — AdBlock 规则主文件（已有）
- `dist/adblock-YYYYMMDD.txt` — AdBlock 规则归档（已有）
- `dist/dns-blocklist.txt` [NEW] — DNS 规则主文件
- `dist/dns-blocklist-YYYYMMDD.txt` [NEW] — DNS 规则归档
- `dist/dns_summary.json` [NEW] — DNS 规则统计摘要

## 目录结构

### 目录结构总结

本次实施新增 4 个文件，修改 1 个文件，不涉及删除操作。

```
FilterFusion/
├── config/
│   ├── default.header       # [EXISTING] AdBlock 规则头部模板（不变）
│   ├── sources.txt          # [EXISTING] AdBlock 规则源配置（不变）
│   ├── dns.header          # [NEW] DNS 规则头部模板
│   └── dns_sources.txt    # [NEW] DNS 规则源配置
├── scripts/
│   ├── fetch_rules.py      # [EXISTING] AdBlock 规则抓取（不变）
│   ├── merge_rules.py      # [EXISTING] AdBlock 规则合并（不变）
│   ├── fetch_dns_rules.py  # [NEW] DNS 规则抓取脚本
│   └── merge_dns_rules.py  # [NEW] DNS 规则合并脚本
├── dist/
│   ├── adblock-main.txt    # [EXISTING] AdBlock 规则主文件（不变）
│   └── dns-blocklist.txt  # [NEW] DNS 规则主文件
└── .github/workflows/
    └── daily-update.yml    # [MODIFY] 添加 DNS 规则处理步骤
```

### 文件详细说明

1. **`config/dns_sources.txt`** [NEW]

- 用途：定义 DNS 拦截规则的源
- 功能：配置格式与 `sources.txt` 一致（`名称 > URL`），支持启用/禁用
- 实现要求：复用 `fetch_rules.py` 中的 `load_sources()` 解析逻辑

2. **`config/dns.header`** [NEW]

- 用途：DNS 规则文件的头部模板
- 功能：定义输出文件的描述信息，使用占位符动态注入
- 实现要求：不包含 `[Adblock Plus 2.0]` 和 `{CHECKSUM}`（DNS 规则不需要 ABP 校验和）

3. **`scripts/fetch_dns_rules.py`** [NEW]

- 用途：异步抓取 DNS 规则源
- 功能：复用 `fetch_rules.py` 的异步抓取逻辑，修改文件路径和元数据文件
- 实现要求：
    - 读取 `config/dns_sources.txt`
    - 规则保存到 `rules/dns_{safe_name}.txt`
    - 元数据保存到 `rules/dns_fetch_meta.json`
    - 复用 httpx.AsyncClient + asyncio.gather 并发下载

4. **`scripts/merge_dns_rules.py`** [NEW]

- 用途：合并和去重 DNS 规则
- 功能：读取抓取产物，去重，输出标准格式
- 实现要求：
    - 不需要复杂的规则分类（DNS 规则是 AdBlock 规则的子集）
    - 主要做去重：例外规则（`@@` 开头）和普通规则
    - 输出到 `dist/dns-blocklist.txt` 和按日期归档的文件
    - 保存摘要到 `dist/dns_summary.json`

5. **`.github/workflows/daily-update.yml`** [MODIFY]

- 用途：CI/CD 工作流配置
- 功能：添加 DNS 规则抓取和合并步骤
- 实现要求：在现有步骤后添加两个 step（fetch_dns_rules、merge_dns_rules）

## 关键代码结构（可选）

由于 DNS 规则合并逻辑比 AdBlock 规则简单，不需要复杂的类型定义。以下是关键接口：

### DNS 规则合并器核心接口

```python
class DnsRuleMerger:
    """DNS 规则合并器：读取抓取产物 → 去重 → 输出标准格式。"""

    def __init__(self) -> None:
        """初始化合并器，设置项目根目录、分发目录、规则目录。"""

    def load_metadata(self) -> dict[str, Any]:
        """加载 DNS 规则抓取元数据。"""

    def load_header_template(self) -> str:
        """加载 DNS 规则头部模板。"""

    def merge(self) -> None:
        """执行 DNS 规则合并主流程。"""

    def save_summary(self, version: str, source_stats: list[dict[str, Any]], processing_time: float) -> None:
        """保存 DNS 规则摘要信息到 JSON 文件。"""
```

### DNS 规则抓取器核心接口（复用 RuleFetcher）

由于 `fetch_dns_rules.py` 与 `fetch_rules.py` 逻辑高度相似，可以考虑：

1. **方案 A**：直接复制 `fetch_rules.py` 并修改路径（简单直接，但代码重复）
2. **方案 B**：重构 `fetch_rules.py` 为可配置的类（更优雅，但需要修改现有代码）

**建议**：采用方案 A（直接复制并修改），原因：

- 风险低：不修改现有代码，避免引入回归问题
- 简单直接：DNS 规则抓取与 AdBlock 规则抓取逻辑独立
- 后续优化：如果项目需要扩展更多规则类型，再考虑重构为通用抓取器