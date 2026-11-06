# CI/CD

FilterFusion 使用 GitHub Actions 实现完全自动化的规则更新和发布流程。

## 工作流一览

| 工作流 | 文件 | 触发方式 | 频率 |
|--------|------|----------|------|
| 每日更新 | `daily-update.yaml` | `cron` + 手动 | 每天 |
| 双周快照 | `weekly-release.yml` | `cron` + 手动 | 每两周（奇数 ISO 周） |

> **注**：`daily-update.yaml` 已整合 GitHub Pages 部署步骤（原 `static.yml`），规则文件更新后自动部署，无需单独的工作流。

## 每日更新（`daily-update.yaml`）

### 功能

1. **抓取规则** — 单进程执行 `python -m scripts.run_all`，内部异步并发抓取 AdBlock + DNS 规则源
2. **合并规则** — 按类别合并去重，生成最终规则文件
3. **校验** — 检查文件非空，再由 `scripts.validate_dist` 校验规则数、Checksum 与头部字段
4. **提交推送** — 自动提交到 `main` 分支

### 执行流程

```
cron 触发（每天）
    ↓
检出代码（fetch-depth: 1）
    ↓
设置 Python 3.14 + uv
    ↓
──── 异步并发（单进程）────
│ 抓取 AdBlock 规则      │
│ 抓取 DNS 规则         │
──── 并发结束 ────
    ↓
合并所有规则（merge_all.py）
    ↓
校验规则文件 + 产物完整性校验
    ↓
提交并推送（filterfusion-bot）
```

### 并发控制

- 使用 `concurrency` 组，防止同一时间多次触发导致竞态
- 两个工作流共用同一并发组，排队执行而非取消，避免同时改 `main`

### 清理策略

- 提交前自动清理临时规则文件和 `__pycache__`
- 保持 `scripts/` 目录干净

## 双周快照（`weekly-release.yml`）

### 功能

1. **创建 Release Tag** — 格式 `YYYY.MM.DD`
2. **生成 Release Notes** — 自动汇总本期规则统计
3. **打包规则文件** — 将所有 `.txt` 文件打包到 Release

### Tag 格式

```
YYYY.MM.DD
例：2026.06.23
```

### Release 标题

```
FilterFusion 规则快照 · YYYY.MM.DD
例：FilterFusion 规则快照 · 2026.11.06
```

### 注意事项

- 创建 Tag 前通过 `git ls-remote --tags` 查询远程同名 Tag（浅克隆不拉 tags），存在则删除重建
- 本地推送代码前请先 `git fetch` + `git pull --rebase origin main`（每日 CI 会自动推送）

## GitHub Pages 部署（整合到 `daily-update.yaml`）

> **历史说明**：原 `static.yml` 工作流已删除，部署步骤整合到 `daily-update.yaml` 中。

### 部署流程

`daily-update.yaml` 在规则文件更新后自动部署到 GitHub Pages：

1. **配置 Pages** — `actions/configure-pages@v6`
2. **禁用 Jekyll** — 创建 `dist/.nojekyll` 文件
3. **上传产物** — `actions/upload-pages-artifact@v5`
4. **部署 Pages** — `actions/deploy-pages@v5`
5. **刷新 CDN 缓存** — 调用 Cloudflare `purge_cache`（未配置 Secret 时自动跳过）

### 优化配置

- **单 Job 架构** — 抓取、合并、推送、部署在同一个 Job 中完成，消除 Runner 冷启动和重复 checkout 开销（节省 ~40-50 秒）
- **条件部署** — 仅当规则文件有变更时才执行部署步骤
- **并发控制** — 两个工作流共用 `group: repo-write, cancel-in-progress: false`（排队而非取消）

### 自定义域名

项目使用自定义域名，配置在仓库根目录的 `CNAME` 文件中（Pages 绑定用）。

> 具体域名请直接查看仓库中的 `CNAME` 文件。

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
  pages: write
  id-token: write
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
