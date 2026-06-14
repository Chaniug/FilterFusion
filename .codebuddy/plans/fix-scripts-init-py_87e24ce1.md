---
name: fix-scripts-init-py
overview: 为 scripts/ 目录创建 __init__.py，修复 daily-update.yml 中 python -m 调用的模块导入问题，并优化 continue-on-error 避免隐藏真实错误。
todos:
  - id: create-init-py
    content: 创建 scripts/__init__.py 空文件，使 scripts 成为正式 Python 包
    status: completed
  - id: fix-workflow
    content: "移除 daily-update.yml 中 fetch 步骤的 continue-on-error: true"
    status: completed
---

## 问题描述

用户将 config/sources 重命名为 config/sources.txt 并同步更新了代码后，GitHub Actions 的 daily-update.yml 工作流运行报错。

## 根因分析

1. **核心问题**：daily-update.yml 使用 `python -m scripts.fetch_rules` 和 `python -m scripts.merge_rules` 运行脚本。`-m` 参数要求 `scripts/` 目录是一个合法的 Python 包，但项目全局缺少 `__init__.py` 文件，导致在 GitHub Actions Ubuntu runner 上 Python 无法正确识别 scripts 为包。
2. **次要问题**：fetch 步骤设置了 `continue-on-error: true`，当 fetch 因上述问题失败时不会终止工作流，merge 步骤因找不到 `fetch_meta.json` 而报错退出，掩盖了真实根因。

## 修复内容

- 创建 `scripts/__init__.py`（空文件），使 scripts 成为正式 Python 包
- 移除 daily-update.yml 中 fetch 步骤的 `continue-on-error: true`，让错误直接暴露便于排查

## 技术方案

### 修复一：创建 scripts/**init**.py

在 `scripts/` 目录下创建空的 `__init__.py` 文件。这是 Python 包的标准约定，使 `python -m scripts.xxx` 能够正确解析模块路径。

- **文件路径**：`scripts/__init__.py`
- **内容**：空文件

### 修复二：移除 continue-on-error

在 `daily-update.yml` 第 36 行移除 `continue-on-error: true`，让 fetch 步骤失败时立即终止工作流并输出清晰的错误信息。

### 影响范围

- **新增文件**：`scripts/__init__.py`
- **修改文件**：`.github/workflows/daily-update.yml`
- **无破坏性变更**，仅修复运行时错误