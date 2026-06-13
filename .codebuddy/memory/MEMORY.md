# FilterFusion 项目长期记忆

## 项目概述
FilterFusion 是一个广告过滤规则聚合工具，从多源获取过滤规则，合并去重后分发。

## 技术决策
- **Release 命名**: Tag 格式 `YYYY.MM.DD`，Release 标题 `FilterFusion Weekly · YYYY.MM.DD`
- **Release 验证**: 使用 GitHub Actions 自动创建 Tag 实现 "Verified" 徽章（GitHub 内置验证），不使用 GPG 签名
- **GitHub Actions 权限**: `permissions: contents: write` 用于允许自动创建 Tag 和 Release
- **Checksum 格式**: 使用 ABP 标准 MD5 + Base64（24字符），而非 SHA-256。实现在 `scripts/merge_rules.py` 第 288-293 行

## 环境配置
- **PowerShell**: 需禁用 `Microsoft.WinGet.CommandNotFound` 模块，在 `$PROFILE` 中添加 `Remove-Module Microsoft.WinGet.CommandNotFound -ErrorAction SilentlyContinue`

## Python 类型注解升级 (2026-06-13)
- Python 版本要求：3.8 → 3.10+
- 依赖 `requests>=2.31.0`（放宽版本约束）
- 所有脚本添加完整类型注解（`scripts/fetch_rules.py`、`scripts/merge_rules.py`）
- 创建 `pyproject.toml`：项目元数据、mypy/basedpyright/pytest/black/isort 配置
- 创建 `requirements-dev.txt`：开发依赖
- basedpyright 验证通过：0 errors, 0 warnings, 0 notes
- 文档更新（README.md、README_EN.md、PROJECT_DOCS.md）Python 版本要求
- GitHub Actions 兼容性验证通过（Python 3.12 ≥ 3.10）
- Windows 本地运行时需 `$env:PYTHONIOENCODING='utf-8'` 处理 emoji

## 关键文件
- `.github/workflows/daily-update.yml` — 每日自动更新工作流
- `.github/workflows/weekly-release.yml` — 每周自动发布工作流
- `scripts/` — 核心脚本目录
- `config/` — 规则源配置、头部模板
- `rules/` — 规则抓取元数据（fetch_meta.json）
- `dist/` — 生成的规则文件（adblock-*.txt, summary.json）
- `PROJECT_DOCS.md` — 完整项目文档
- `pyproject.toml` — 现代 Python 项目配置
