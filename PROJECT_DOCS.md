# FilterFusion 项目文档

> **版本**: 1.0 | **最后更新**: 2026-06-13 | **许可证**: MIT

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 项目架构](#2-项目架构)
- [3. 目录结构](#3-目录结构)
- [4. 核心组件详解](#4-核心组件详解)
  - [4.1 规则源配置 (`config/sources.txt`)](#41-规则源配置-configsourcestxt)
  - [4.2 抓取脚本 (`scripts/fetch_rules.py`)](#42-抓取脚本-scriptsfetch_rulespy)
  - [4.3 合并脚本 (`scripts/merge_rules.py`)](#43-合并脚本-scriptsmerge_rulespy)
  - [4.4 输出头部模板 (`config/default.header`)](#44-输出头部模板-configdefaultheader)
- [5. 工作流程](#5-工作流程)
  - [5.1 本地使用](#51-本地使用)
  - [5.2 自动流水线 (GitHub Actions)](#52-自动流水线-github-actions)
- [6. 输出产物](#6-输出产物)
- [7. 部署与订阅](#7-部署与订阅)
- [8. 维护与自定义](#8-维护与自定义)
- [9. 技术细节](#9-技术细节)

---

## 1. 项目概述

FilterFusion 是一个**自动化广告过滤规则聚合工具**，由 [Chaniug](https://github.com/Chaniug) 开发维护。

### 核心能力

| 能力 | 说明 |
|------|------|
| 多源聚合 | 自动从 AdGuard Mobile、AdGuard Chinese、Chaniug AdSuper 等多个源抓取规则 |
| 智能去重 | 基于 Unicode NFKC 规范化 + 类型化键值实现全局去重 |
| 分类输出 | 按规则语义（例外/HTML过滤/正则/特殊参数/普通屏蔽）分类组织 |
| 自动更新 | GitHub Actions 每日自动抓取、合并、发布 |
| 多 CDN 分发 | 支持 GitHub Raw / jsDelivr / FastGit 等多条订阅线路 |

### 适用范围

- **uBlock Origin** (桌面版/移动版)
- **AdGuard** (桌面版/移动版/浏览器扩展)
- **Adblock Plus** (ABP)
- **Brave 浏览器**
- 任何兼容 Adblock Plus 语法的广告拦截工具

---

## 2. 项目架构

### 数据流图

```
┌──────────────────┐
│  config/sources.txt  │  ← 规则源 URL 配置
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│  fetch_rules.py  │ ──→ │  rules/*.txt      │  ← 原始抓取文件
│  (规则抓取)       │     │  rules/fetch_meta │  ← 抓取元数据
└──────────────────┘     └────────┬─────────┘
                                  │
                                  ▼
┌──────────────────┐     ┌───────────────────────┐
│  merge_rules.py  │ ──→ │ dist/adblock-YYYYMMDD.txt │
│  (合并去重)       │     │ dist/adblock-main.txt     │
│                  │     │ dist/summary.json         │
└──────────────────┘     └───────────────────────────┘
```

### 四阶段流水线

```
阶段 1: 配置 ──→ 阶段 2: 抓取 ──→ 阶段 3: 合并去重 ──→ 阶段 4: 输出发布
```

| 阶段 | 输入 | 处理 | 输出 |
|------|------|------|------|
| 配置 | `config/sources.txt` | 定义规则源 URL、名称、启用状态 | — |
| 抓取 | 各源 URL | HTTP GET 下载，计算 SHA256 哈希 | `rules/*.txt`, `rules/fetch_meta.json` |
| 合并 | 原始规则文件 + header 模板 | Unicode 规范化 → 分类 → 去重 → 排序 | `dist/adblock-YYYYMMDD.txt` |
| 输出 | 合并结果 | 写入主文件、摘要文件 | `dist/adblock-main.txt`, `dist/summary.json` |

---

## 3. 目录结构

```
FilterFusion/
├── .github/workflows/         # CI/CD 工作流
│   ├── daily-update.yml       # 每日自动更新
│   ├── weekly-release.yml     # 每周 Release 打包
│   └── static.yml             # GitHub Pages 部署
├── assets/
│   └── preview.png            # 项目预览图
├── config/
│   ├── default.header         # 输出规则文件头部模板
│   └── sources.txt            # 规则源配置
├── dist/                      # 输出产物（自动生成）
│   ├── adblock-main.txt       # 最新主规则文件
│   ├── adblock-YYYYMMDD.txt   # 按日期归档的规则文件（保留近3天）
│   └── summary.json           # 统计摘要
├── rules/                     # 抓取缓存（自动生成）
│   ├── *.txt                  # 各源下载的原始规则文件
│   └── fetch_meta.json        # 抓取元数据
├── scripts/
│   ├── fetch_rules.py         # 规则抓取脚本
│   └── merge_rules.py         # 规则合并去重脚本
├── .gitignore
├── _cdnauth.txt               # CDN 认证令牌
├── CNAME                      # 自定义域名: ad.valk.ccwu.cc
├── LICENSE                    # MIT 许可证
├── README.md                  # 中文说明文档
├── README_EN.md               # 英文说明文档
└── requirements.txt           # Python 依赖
```

---

## 4. 核心组件详解

### 4.1 规则源配置 (`config/sources.txt`)

**文件格式**: 纯文本，一行一个规则源，格式为 `名称 > 订阅地址`。

```txt
# FilterFusion 规则源配置
# 格式: 名称 > 订阅地址
# 开启: 直接写一行
# 关闭: 行首加 #

AdGuard Mobile > https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_11_Mobile/filter.txt
AdGuard Chinese > https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_224_Chinese/filter.txt
Chaniug AdSuper > https://raw.githubusercontent.com/Chaniug/AdSuper/refs/heads/master/adnew.txt
Adguard Extra > https://filters.adtidy.org/android/filters/5_optimized.txt

# 下面是关闭的源（去掉行首 # 即可开启）：
# EasyList > https://easylist.to/easylist.txt
```

**配置规则**：
- **启用规则源**: 直接写一行 `名称 > 订阅地址`
- **禁用规则源**: 在行首加 `#`（如 `# EasyList > https://...`）
- **纯注释**: 以 `#` 开头且不含 `>` 的行会被忽略
- **空行**: 会被自动跳过

当前配置了 **4 个启用的规则源**：

| 源名称 | 类型 | 规则量级 |
|--------|------|----------|
| AdGuard Mobile | AdGuard 移动端过滤规则 | ~数千条 |
| AdGuard Chinese | AdGuard 中文规则 | ~21,000+ 条 |
| Chaniug AdSuper | 作者自维护补充规则 | ~60 条 |
| Adguard Extra | AdGuard 额外优化规则 | ~15 条 |

### 4.2 抓取脚本 (`scripts/fetch_rules.py`)

**类**: `RuleFetcher`

**核心逻辑**：
1. 读取 `config/sources.txt`，获取所有已启用的规则源
2. 对每个源发起 HTTP GET 请求下载规则文件
3. 计算下载内容的 SHA256 哈希值
4. 保存到 `rules/` 目录（文件名由源名称安全转换而来）
5. 写入元数据到 `rules/fetch_meta.json`

**关键特性**：
- **重试机制**: 最多 3 次重试，递增超时（30s → 45s → 60s）
- **增量更新**: 通过哈希对比可判断源是否有更新
- **元数据记录**: 保存每次抓取的时间戳、状态、文件哈希

**命令行使用**:
```bash
python scripts/fetch_rules.py
```

### 4.3 合并脚本 (`scripts/merge_rules.py`)

**类**: `RuleMerger`

**核心逻辑**：
1. 读取 `rules/fetch_meta.json` 获取成功抓取的规则文件
2. 读取 `config/default.header` 获取输出模板
3. 加载所有规则文件内容
4. 按语义对规则**分类分组**

**规则分类**（符合 AdGuard/ABP/uBlock 标准）:

规则按以下优先级分类（避免误判）:

| 优先级 | 分类 | 匹配条件 | 示例 |
|--------|------|----------|------|
| 1 | `comment` | 以 `!` 或 `[` 开头 | `! Title: AdBlock Rules` |
| 2 | `exception` | 以 `@@` 开头（例外规则） | `@@\|\|example.com^\$document` |
| 3 | `regex` | 以 `/` 开头和结尾，含正则特殊字符 | `/\.ads\.example\.com/` |
| 4 | `html_filter` | 含 `#%#`, `#$#`, `#?#`, `scriptlet(` 等 | `example.com#%#//scriptlet(...)` |
| 5 | `element_hide` | 含 `##`（元素隐藏） | `example.com##.ad-banner` |
| 6 | `special` | 选项部分含 `$badfilter`, `$important` 等 | `\|\|ads.com^\$important` |
| 7 | `normal` | 普通域名/路径屏蔽规则 | `\|\|ads.example.com^` |

**分类详细说明**:

- **注释规则**: `!` 开头的注释行或 `[Adblock Plus ...]` 头部声明，仅保留前 10 条
- **例外规则**: `@@` 开头的例外规则，可能包含其他语法（如 `$elemhide`）
- **正则规则**: Adblock Plus 格式的正则表达式，以 `/` 开头和结尾，支持标志 `i`, `g`, `m`
- **HTML/脚本注入**: AdGuard/uBlock 扩展语法，包括 JS 注入（`#%#`）、CSS 注入（`#$#`）、元素筛选（`#?#`）、scriptlet（`#+js(`）
- **元素隐藏**: 标准元素隐藏规则（`##`）或域限制隐藏（`domain##selector`）
- **特殊参数**: 包含特殊修饰符的规则，如 `$badfilter`（禁用）、`$important`（高优先级）、`$csp=`（内容安全策略）
- **普通屏蔽**: 其余有效的屏蔽规则，如 `\|\|domain^`, `\|http://...`, `*pattern*`

5. **全局去重**: 使用 `Unicode NFKC 规范化` 后，以 `类型:规则文本` 为唯一键
6. 各组内**按字母排序**后合并输出
7. 替换 `default.header` 模板中的占位符生成最终文件

**命令行使用**:
```bash
python scripts/merge_rules.py
```

### 4.4 输出头部模板 (`config/default.header`)

定义最终规则文件的描述头部，使用以下占位符：

| 占位符 | 说明 |
|--------|------|
| `{VERSION}` | 版本号（日期，如 `20260612`） |
| `{TIMEUPDATED}` | 更新时间 |
| `{CHECKSUM}` | MD5 + Base64 校验和（ABP 标准格式，24字符） |
| `{HOMEPAGE}` | 项目 GitHub 主页 |
| `{LICENSE}` | 许可证声明 |
| `{SOURCE_COUNT}` | 成功抓取的规则源数量 |
| `{SOURCE_LIST}` | 各源的详细描述列表 |
| `{COMBINED_RULES}` | 合并去重后的规则总数 |
| `{TOTAL_RULES}` | 源规则总数（去重前） |
| `{DUPLICATES}` | 重复规则数量（已移除） |

---

## 5. 工作流程

### 5.1 本地使用

```bash
# 1. 克隆仓库
git clone https://github.com/Chaniug/FilterFusion.git
cd FilterFusion

# 2. 安装依赖（仅需 requests）
pip install -r requirements.txt

# 3. 抓取各源的最新规则
python scripts/fetch_rules.py

# 4. 合并去重，生成最终规则文件
python scripts/merge_rules.py

# 5. 输出文件位于 dist/ 目录
# dist/adblock-main.txt  → 可直接导入广告拦截工具
```

**依赖要求**:
- Python 3.10+
- `requests >= 2.31.0`

### 5.2 自动流水线 (GitHub Actions)

项目配置了 3 个自动化工作流：

| 工作流 | 触发条件 | 功能说明 |
|--------|----------|----------|
| **daily-update** | 每天 UTC 0:00 定时 | 自动抓取 → 合并 → 清理过期文件 → 提交推送 |
| **weekly-release** | 每周日 UTC 2:00 定时 | 打包 `dist/` 中所有 `adblock-*.txt` 为 ZIP → 创建 GitHub Release |
| **static** | main 分支 push 时 | 部署 dist/ 目录到 GitHub Pages |

整个流水线**全自动运行**，无需人工干预。维护者只需确保规则源 URL 有效即可。

---

## 6. 输出产物

### `dist/adblock-main.txt`
- 最终合并去重后的主规则文件
- 兼容 Adblock Plus 语法（同时支持 uBlock Origin / AdGuard 扩展语法）
- 按分类组织：例外规则 → HTML/脚本过滤 → 正则 → 特殊参数 → 普通屏蔽

### `dist/adblock-YYYYMMDD.txt`
- 按日期版本归档（保留近 3 天）
- 内容与 `adblock-main.txt` 完全一致
- 用于版本回溯和 Release 打包

### `dist/summary.json`
```json
{
    "version": "20260612",
    "total_source_rules": 30159,
    "unique_rules": 30112,
    "duplicates_removed": 47,
    "merge_time_seconds": 0.17,
    "sources": [ /* 各源统计 */ ]
}
```

---

## 7. 部署与订阅

### 自定义域名
通过 `CNAME` 文件配置: **`ad.valk.ccwu.cc`**

访问该域名将指向项目的 GitHub Pages 站点。

### 订阅地址（可直接在广告拦截工具中使用）

| 线路 | 地址 | 适用场景 |
|------|------|----------|
| GitHub Raw | `https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-main.txt` | 全球通用 |
| jsDelivr CDN | `https://cdn.jsdelivr.net/gh/Chaniug/FilterFusion@main/dist/adblock-main.txt` | **推荐中国大陆用户** |
| GitHub Proxy | `https://ghproxy.com/https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-main.txt` | 备选加速 |

---

## 8. 维护与自定义

### 添加新规则源

编辑 `config/sources.txt`，在文件末尾新增一行：

```txt
你的规则源名称 > https://example.com/filter.txt
```

**格式要求**:
- 一行一个规则源，使用 `>` 分隔名称和 URL
- URL 必须以 `http` 开头
- 名称可包含中文、英文、数字和空格
- 支持 Adblock Plus、uBlock Origin、AdGuard 等主流格式的规则文件

### 禁用规则源

在对应行前面加 `#` 即可禁用，无需删除：

```txt
# AdGuard Chinese > https://...（已禁用）
```

要重新启用，去掉行首的 `#` 即可。

### 修改输出头部

编辑 `config/default.header`，可使用占位符动态注入信息。

### 调整清理策略

编辑 `.github/workflows/daily-update.yml`，修改以下行可调整保留天数和文件匹配模式：

```yaml
# 默认：删除 3 天以前的 adblock-*.txt 文件
find dist -name "adblock-*.txt" -mtime +3 -delete
```

---

## 9. 技术细节

### 去重算法

```
输入规则 → Unicode NFKC 规范化 → 构建键值 "类型:规则文本" → 集合去重
```

使用 `NFKC`（兼容性组合规范化）确保视觉等价但 Unicode 不同的规则被正确识别为重复。例如，全角字母会转换为半角后再比较。

### 规则分类判断

规则按以下优先级分类（符合 AdGuard/ABP/uBlock 标准）:

| 分类 | 优先级 | 判断逻辑 |
|------|--------|----------|
| 注释 | 1 (最高) | 以 `!` 或 `[` 开头 |
| 例外 | 2 | 以 `@@` 开头（例外规则可能包含其他语法） |
| 正则 | 3 | 以 `/` 开头和结尾，含正则特殊字符（`.`, `*`, `+`, `?`, `\`, `[`, `]`, `(`, `)`, `{`, `}`, `^`, `$`, `\|`），支持标志 `i`, `g`, `m` |
| HTML过滤 | 4 | 包含 `#%#`, `#$#`, `#?#`, `#+js(`, `scriptlet(` 等 AdGuard/uBlock 扩展语法 |
| 元素隐藏 | 5 | 包含 `##`（元素隐藏规则） |
| 特殊 | 6 | 选项部分（`$` 之后）含 `badfilter`, `important`, `csp=` 等修饰符 |
| 普通 | 7 (最低) | 其余有效的屏蔽规则 |

**注意事项**:
- 分类优先级避免误判（如 `@@` 例外规则可能包含 `$elemhide`，应优先识别为例外）
- 正则规则验证确保不是普通路径（如 `/ads.html`）
- HTML 过滤规则必须在元素隐藏之前判断（如 `#%#` 不是元素隐藏）
- 特殊参数判断限定在选项部分（`$` 之后），避免误判规则路径

### 文件哈希校验

- 每个源下载后计算 **SHA256** 哈希，存入 `fetch_meta.json`
- 用于增量判断源是否有更新
- 最终合并文件整体计算 SHA256 校验和，写入文件头部，方便用户验证文件完整性

### 安全性

- 脚本仅执行 HTTP GET 下载和本地文件读写，无系统调用
- 不执行或 eval 任何下载的规则内容
- 抓取超时 + 重试机制避免无限等待

---

> **项目主页**: [https://github.com/Chaniug/FilterFusion](https://github.com/Chaniug/FilterFusion)
>
> **许可证**: MIT License (Copyright © 2025 Chaniug)
