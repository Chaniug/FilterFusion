# FilterFusion 长期记忆

## 项目概况
- 广告过滤规则聚合工具，每日 CI 抓取 4 个规则源 → 分类去重 → 输出标准 ABP 格式
- 维护者：Chaniug，GitHub 仓库 Chaniug/FilterFusion
- 订阅域名：ad.valk.ccwu.cc（GitHub Pages + CNAME）

## 技术栈（2026-06-18 第二轮优化后）
- Python >=3.13（CPython 3.13 specializing interpreter ~5-10% 性能提升）
- 运行时依赖：`httpx[http2]>=0.27.0`（替代 requests，异步 + HTTP/2 多路复用）
- CI 包管理：uv（`astral-sh/setup-uv@v8.2.0`，依赖安装 10-100 倍加速，node24 运行时）
- 输出产物位置不变：`dist/adblock-main.txt`、`dist/adblock-YYYYMMDD.txt`、`dist/summary.json`

## CI 环境约定（2026-06-18 多轮修复后确定）
- **依赖安装**: `uv venv && uv pip install -r requirements.txt`（不构建项目包，避免 setuptools 多目录冲突）
- **脚本执行**: `uv run --no-project python -m scripts.xxx`（跳过项目构建，仅使用 venv）
- **setup-uv 版本**: `@v8.2.0`（node24 运行时；注意 `@v8` 短标签不存在，必须用完整版本号）
- **pyproject.toml**: `[tool.setuptools.packages.find]` 配置 `include = ["scripts*"]`；`license = "MIT"` 字符串格式

## 优化历史
- 2026-06-16 第一轮：去重键简化、ASCII 快速路径、预编译正则、fetch-depth 降级、concurrency 控制
- 2026-06-18 第二轮：Python 3.13 升级、httpx 异步重写、merge 热路径常量提升、format_map 替代链式 replace、uv 加速 CI、static.yml paths 过滤
- 2026-06-18 第三轮（CI 修复）：解决 uv + Python 3.13 在 GitHub Actions 上的 4 轮连环报错（`--system`、`uv sync`、`uv run` 构建失败、Node 20 弃用），最终确定为 `uv venv` + `uv run --no-project` 方案

## 约定
- Checksum 算法：ABP 标准 MD5 + Base64（24 字符）
- header 模板用 `format_map` + `_SafeDict`（`__missing__` 保持 `{CHECKSUM}` 占位符延后填充）
- 规则分类用 `RuleType(StrEnum)` 枚举，类级 `_HTML_FILTER_RE`/`_SPECIAL_RE`/`_REGEX_CHAR_RE` 预编译正则
- 所有 `open()` 必须指定 `encoding='utf-8'`（Windows 本地运行兼容）
- Git 提交身份：FilterFusion Bot / filterfusion-bot@users.noreply.github.com
- `setup-uv` 引用格式：必须用完整版本号如 `@v8.2.0`，不能用 `@v8`（该仓库没有短标签）

## 环境注意
- Windows 本地运行需 `$env:PYTHONIOENCODING='utf-8'`（已通过显式 encoding 缓解）
- PowerShell 需禁用 Microsoft.WinGet.CommandNotFound 模块
- 本地无 Python 3.13 + httpx 时，basedpyright 会报 UTC/StrEnum/httpx/type 语句解析错误，属环境问题非代码问题
- 本地 Python 环境：3.14（`requires-python = ">=3.13"` 覆盖，无需调整约束；CI 仍锁定 3.13 以保证可重现性）
