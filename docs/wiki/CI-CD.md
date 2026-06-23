# CI/CD

FilterFusion 使用 GitHub Actions 实现完全自动化的规则更新和发布流程。

## 工作流一览

| 工作流 | 文件 | 触发方式 | 频率 |
|--------|------|----------|------|
| 每日更新 | `daily-update.yml` | `cron` + 手动 | 每天 |
| 每周发布 | `weekly-release.yml` | `cron` + 手动 | 每周 |
| Pages 部署 | `static.yml` | 推送 `main` 分支 | 每次推送 |

## 每日更新（`daily-update.yml`）

### 功能

1. **抓取规则** — 同时抓取 AdBlock + DNS 规则源（Shell 后台任务并行）
2. **合并规则** — 按类别合并去重，生成最终规则文件
3. **校验** — 检查生成的规则文件是否有效
4. **提交推送** — 自动提交到 `main` 分支

### 执行流程

```
cron 触发（每天）
    ↓
检出代码（fetch-depth: 1）
    ↓
设置 Python 3.14 + uv
    ↓
──── 并行 ────
│ 抓取 AdBlock 规则      │
│ 抓取 DNS 规则         │
──── 并行结束 ────
    ↓
合并所有规则（merge_all.py）
    ↓
校验规则文件
    ↓
提交并推送（filterfusion-bot）
```

### 并发控制

- 使用 `concurrency` 组，防止同一时间多次触发导致竞态
- 如果上次运行未完成，自动取消本次运行

### 清理策略

- 提交前自动清理临时规则文件和 `__pycache__`
- 保持 `scripts/` 目录干净

## 每周发布（`weekly-release.yml`）

### 功能

1. **创建 Release Tag** — 格式 `YYYY.MM.DD`
2. **生成 Release Notes** — 自动汇总本周的变更
3. **打包规则文件** — 将所有 `.txt` 文件打包到 Release

### Tag 格式

```
YYYY.MM.DD
例：2026.06.23
```

### Release 标题

```
FilterFusion Weekly · YYYY.MM.DD
例：FilterFusion Weekly · 2026.06.23
```

### 注意事项

- 创建 Tag 前会自动检查并删除已存在的同名 Tag（避免 fatal 错误）
- 需要先 `git pull origin main` 确保本地分支最新

## Pages 部署（`static.yml`）

### 功能

将 `dist/` 目录部署到 GitHub Pages，提供规则文件下载。

### 优化配置

- **`.nojekyll` 文件** — 跳过 Jekyll 构建，加速部署
- **`cancel-in-progress: true`** — 避免排队等待
- **`paths` 过滤** — 仅 `dist/**` 变更时触发，避免脚本/文档变更触发无意义部署

### 自定义域名

项目使用自定义域名，配置在 `CNAME` 文件中：

```
chaniug.github.io
```

> 实际域名请在 `CNAME` 文件中确认。

## 手动触发

两个工作流都支持手动触发：

1. 进入 GitHub 仓库页面
2. 点击「Actions」选项卡
3. 选择对应工作流
4. 点击「Run workflow」
5. 选择分支（通常 `main`），点击确认

## 权限要求

工作流需要以下权限：

```yaml
permissions:
  contents: write
```

用于自动提交规则更新和创建 Release Tag。

## 依赖版本

| 依赖 | 版本 | 说明 |
|------|------|------|
| `actions/checkout` | `v7.0.0` | 检出代码 |
| `astral-sh/setup-uv` | `v8.2.0` | 安装 uv（必须用完整版本号，`@v8` 不存在） |
| `actions/configure-pages` | `v6` | 配置 Pages |
| `upload-pages-artifact` | `v5` | 上传 Pages 产物 |
| `deploy-pages` | `v5` | 部署 Pages |
| Python | `3.14` | 运行时版本 |

## 故障排查

### 工作流运行失败

1. 检查「Actions」选项卡中的错误日志
2. 确认 `config/sources.yaml` 中的 URL 是否可访问
3. 确认 `requirements.txt` 中的依赖是否正确

### Release 创建失败

- 检查是否已存在同名 Tag
- 工作流会自动删除旧 Tag，如果仍失败，手动删除：

```bash
git tag -d YYYY.MM.DD
git push origin :refs/tags/YYYY.MM.DD
```

## 下一步

- 本地运行和测试 → [安装与快速开始](/wiki/安装与快速开始)
- 了解项目架构 → [开发者文档](/wiki/开发者文档)
