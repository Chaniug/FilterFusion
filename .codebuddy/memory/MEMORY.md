# FilterFusion 项目长期记忆

## 项目概述
FilterFusion 是一个广告过滤规则聚合工具，从多源获取过滤规则，合并去重后分发。

## 技术决策
- **Release 命名**: Tag 格式 `YYYY.MM.DD`，Release 标题 `FilterFusion Weekly · YYYY.MM.DD`
- **Release 验证**: 使用 GitHub Actions 自动创建 Tag 实现 "Verified" 徽章（GitHub 内置验证），不使用 GPG 签名
- **GitHub Actions 权限**: `permissions: contents: write` 用于允许自动创建 Tag 和 Release

## 环境配置
- **PowerShell**: 需禁用 `Microsoft.WinGet.CommandNotFound` 模块，在 `$PROFILE` 中添加 `Remove-Module Microsoft.WinGet.CommandNotFound -ErrorAction SilentlyContinue`

## 关键文件
- `.github/workflows/weekly-release.yml` — 每周自动发布工作流
- `scripts/` — 核心脚本目录
- `config/` — 规则源配置文件
- `rules/` — 规则集 JSON
- `PROJECT_DOCS.md` — 完整项目文档
