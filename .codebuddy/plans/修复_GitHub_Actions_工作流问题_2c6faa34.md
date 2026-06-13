---
name: 修复 GitHub Actions 工作流问题
overview: 修复 daily-update.yml 的 git push 失败处理逻辑，以及在 weekly-release.yml 中添加 git pull 确保基于最新 commit 打标签
todos:
  - id: fix-daily-push
    content: 修复 daily-update.yml 的 git push 逻辑，移除错误的 || echo 容错，确保 rebase 失败时报错终止
    status: completed
  - id: fix-weekly-pull
    content: 修复 weekly-release.yml，在创建 Tag 前添加 git pull origin main 拉取最新代码
    status: completed
  - id: verify-syntax
    content: 验证两个 YAML 文件的语法正确性，确认 workflow 配置无误
    status: completed
    dependencies:
      - fix-daily-push
      - fix-weekly-pull
---

## 产品概述

修复 FilterFusion 项目中 GitHub Actions 工作流的两个逻辑问题，确保自动化流程稳定可靠。

## 核心功能

- 修复 daily-update.yml 中 git push 逻辑：rebase 失败时当前仅打印警告但继续 push，可能导致 non-fast-forward 错误
- 修复 weekly-release.yml 中标签创建逻辑：创建 Tag 前未 pull 最新代码，可能基于旧 commit 打标签

## 技术栈

- GitHub Actions 工作流 YAML 配置
- Git 命令行操作

## 实现方案

### 问题一：daily-update.yml 的 git push 逻辑修复

**当前问题**：第 73 行使用 `||` 操作符，rebase 失败时只打印警告但退出码为 0，后续 `git push` 会继续执行，若 rebase 实际失败则 push 会被拒绝。

**修复方案**：将 git 操作改为脚本块，明确处理 rebase 失败的情况：

1. 执行 `git pull --rebase origin main`
2. 若失败，终止流程（避免基于过期代码 push）
3. 检查是否有变更需要提交
4. 提交并 push

**关键代码修改**：

```
- name: 📤 提交变更
  run: |
    git config user.name "FilterFusion Bot"
    git config user.email "filterfusion-bot@users.noreply.github.com"
    
    # 拉取最新代码
    git pull --rebase origin main
    
    git add dist
    if git diff-index --quiet HEAD; then
      echo "没有规则变更，跳过提交"
    else
      git commit -m "FilterFusion自动更新: $(date -u +'%Y-%m-%d %H:%M UTC')"
      git push
    fi
```

### 问题二：weekly-release.yml 添加 git pull

**当前问题**：第 43 行直接创建 Tag，但未先 pull 最新代码，若 daily-update 在周日 08:00 推送了新提交，weekly-release 可能基于旧 commit 打标签。

**修复方案**：在"自动生成版本号并创建 Tag"步骤中，创建 Tag 前先执行 `git pull origin main`。

**关键代码修改**：在 `steps.version` 的 run 块中，在 `git tag "$DATE"` 之前添加：

```
git pull origin main
```

## 实现注意事项

- daily-update.yml 去掉 `|| echo` 的容错写法，让 rebase 失败时报错终止流程更合理（次日会自动重试）
- weekly-release.yml 的 pull 操作应在配置 git 身份之后、创建 tag 之前执行
- 两个修改都不影响工作流的触发时间和频率

## 架构设计

本次修改为工作流配置修复，不涉及系统架构变更。

## 目录结构

本次修改仅涉及两个文件：

```
.github/workflows/
├── daily-update.yml    [MODIFY] 修复 git push 逻辑，移除错误的容错处理
└── weekly-release.yml   [MODIFY] 在创建 Tag 前添加 git pull 步骤
```