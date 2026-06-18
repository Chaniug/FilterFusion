---
name: reorganize-project-folders
overview: 归拢整理项目文件夹：将 rules/ 合并到 scripts/，dist/ 下的 JSON 移到 config/，根目录零散文件归位，保持文件夹数量不增加。
todos:
  - id: move-files
    content: 移动 6 个文件到目标目录并删除 rules/ 空目录
    status: completed
  - id: update-scripts-paths
    content: 修改 4 个 Python 脚本中的 rules_dir 路径和 summary JSON 写入路径，更新 print 文本
    status: completed
    dependencies:
      - move-files
  - id: update-gitignore
    content: 移除 .gitignore 中的 rules/ 忽略规则
    status: completed
  - id: update-workflow
    content: 更新 daily-update.yml 的 git checkout 和 git add 命令，覆盖 config 和 scripts
    status: completed
    dependencies:
      - move-files
  - id: update-docs
    content: 更新 PROJECT_DOCS.md 目录结构图和 PROJECT_LOG.md 路径引用
    status: completed
    dependencies:
      - move-files
  - id: verify
    content: 全局搜索残留的旧路径引用，确认无遗漏
    status: completed
    dependencies:
      - update-scripts-paths
      - update-workflow
      - update-docs
---

## 项目目录结构整理

将零散分布在各处的 JSON 元数据文件归拢到对应职责目录，删除功能已消失的 `rules/` 空壳目录，让 `dist/` 只保留纯规则文件，使项目结构更清晰。

### 变更概览

| 操作 | 内容 |
| --- | --- |
| 移动 | `rules/fetch_meta.json`、`rules/dns_fetch_meta.json` → `scripts/` |
| 删除 | `rules/` 空目录 |
| 移动 | `dist/summary.json`、`dist/dns_summary.json` → `config/` |
| 移动 | `_cdnauth.txt`（根目录）→ `config/` |
| 移动 | `PROJECT_DOCS.md`（根目录）→ `docs/` |


### 最终效果

- 文件夹数从 6 变为 5（assets、config、dist、docs、scripts）
- `dist/` 纯净：只有 `.txt` 规则文件
- 根目录零散文件减少 2 个

## 实现方案

### 策略

纯文件搬迁 + 字符串路径替换，不涉及逻辑变更。所有脚本内 `self.rules_dir` 变量名保留不变（仅改初始化字符串），最小化 diff。

### 修改清单

#### 1. 文件移动（6 个文件 + 1 个目录删除）

```
rules/fetch_meta.json     → scripts/fetch_meta.json
rules/dns_fetch_meta.json → scripts/dns_fetch_meta.json
del rules/
dist/summary.json         → config/summary.json
dist/dns_summary.json     → config/dns_summary.json
_cdnauth.txt              → config/_cdnauth.txt
PROJECT_DOCS.md           → docs/PROJECT_DOCS.md
```

#### 2. scripts/fetch_rules.py（5 处）

- L40: `self.project_root / "rules"` → `self.project_root / "scripts"`
- L41: 删除 `self.rules_dir.mkdir(parents=True, exist_ok=True)`（scripts/ 已存在且被 git 追踪）
- L44: print 文本 `规则目录` 不变（变量保留）
- L42/L114: `self.rules_dir` 变量引用不变

#### 3. scripts/fetch_dns_rules.py（5 处）

- L40: 同 fetch_rules.py L40
- L41: 删除 mkdir
- L42/L44/L114: 不变

#### 4. scripts/merge_rules.py（6 处）

- L73: `self.project_root / "rules"` → `self.project_root / "scripts"`
- L76: print 不变（变量引用）
- L84/L227: `self.rules_dir` 引用不变
- L416: `self.dist_dir / "summary.json"` → `self.project_root / "config" / "summary.json"`
- L420: `"📊 摘要信息已保存至: dist/summary.json"` → `"📊 摘要信息已保存至: config/summary.json"`

#### 5. scripts/merge_dns_rules.py（6 处）

- L36: 同 merge_rules.py L73
- L39: print 不变
- L48/L113: 引用不变
- L279: `self.dist_dir / "dns_summary.json"` → `self.project_root / "config" / "dns_summary.json"`
- L283: `"📊 DNS 摘要信息已保存至: dist/dns_summary.json"` → `"📊 DNS 摘要信息已保存至: config/dns_summary.json"`

#### 6. .gitignore

- L8: 删除 `rules/  # 忽略原始规则文件` 行及其注释

#### 7. .github/workflows/daily-update.yml

- L78: `git checkout origin/main -- ':!dist'` → `git checkout origin/main -- ':!dist' ':!config' ':!scripts'`
- L79: `git add dist` → `git add dist config scripts`

#### 8. docs/PROJECT_DOCS.md（移动后更新自述）

- L133-169: 目录结构图整段重写，反映新布局
- `config/` 块新增 `_cdnauth.txt`、`summary.json`、`dns_summary.json`
- `dist/` 块移除 summary JSON 条目
- 删除 `rules/` 整块，在 `scripts/` 块末尾新增 `fetch_meta.json`、`dns_fetch_meta.json`
- 根目录条目移除 `_cdnauth.txt` 和 `PROJECT_DOCS.md`

#### 9. docs/PROJECT_LOG.md

- L179: `dist/summary.json` → `config/summary.json`