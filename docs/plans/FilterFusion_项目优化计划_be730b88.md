---
name: FilterFusion 项目优化计划
overview: 对 FilterFusion 项目进行全面优化，包括：1) 性能优化（并发下载规则源）；2) GitHub Actions 稳定性增强（失败通知、错误处理）；3) 代码质量改进（修复正则误判bug、固定依赖版本、修正描述文本）；4) 清理冗余配置
todos:
  - id: optimize-fetch
    content: 修改 fetch_rules.py 添加并发下载和 Session 连接池
    status: completed
  - id: fix-merge
    content: 修复 merge_rules.py 第 141 行正则匹配误判 bug
    status: completed
  - id: update-config
    content: 更新 default.header 描述和固定依赖版本
    status: completed
  - id: improve-actions
    content: 改进 GitHub Actions 添加失败通知和错误处理
    status: completed
    dependencies:
      - optimize-fetch
  - id: add-logging
    content: 添加 logging 模块替代 print 语句
    status: completed
    dependencies:
      - optimize-fetch
      - fix-merge
  - id: add-tests
    content: 创建 tests 目录并添加单元测试
    status: completed
    dependencies:
      - optimize-fetch
      - fix-merge
  - id: cleanup
    content: 删除冗余的 jekyll-gh-pages.yml Workflow
    status: completed
---

## 项目概述

优化 FilterFusion 广告过滤规则聚合项目的性能、稳定性和代码质量，使其 GitHub Actions 自动运行更稳健、流程更流畅。

## 核心优化目标

1. **性能优化**：将规则源下载从串行改为并发，减少总下载时间
2. **稳定性增强**：改进 GitHub Actions 错误处理、添加失败通知、避免 Git 冲突
3. **代码质量修复**：修复正则匹配误判 bug、更新不准确配置
4. **可维护性提升**：固定依赖版本、添加日志记录、清理冗余配置

## 功能内容与视觉效果

- 后端 Python 脚本优化，不涉及 UI 改动
- 优化后规则下载时间从约 30 秒降至约 10 秒
- GitHub Actions 运行失败时自动创建 Issue 通知
- 日志持久化到 logs/ 目录，便于调试

## 技术栈选择

- **编程语言**：Python 3.10+（与现有项目一致）
- **核心库**：requests（固定版本）、concurrent.futures（标准库）
- **测试框架**：pytest（新增）
- **CI/CD**：GitHub Actions（改进现有配置）

## 实施方法

### 1. 并发下载规则源

**策略**：使用 `concurrent.futures.ThreadPoolExecutor` 替代串行下载

**高层策略**：
修改 `scripts/fetch_rules.py` 中的 `fetch_all_rules()` 方法，使用线程池并发下载 4 个规则源，同时复用 TCP 连接。

**工作原理**：

- 创建 `ThreadPoolExecutor` 实例，最大线程数设置为规则源数量（4 个）
- 使用 `requests.Session()` 创建会话，复用连接
- 提交所有下载任务到线程池，使用 `as_completed()` 获取结果
- 保留原有的 3 次重试机制和超时递增策略

**关键决策理由**：

- 选择 `ThreadPoolExecutor` 而非 `ProcessPoolExecutor`：I/O 密集型任务，线程足够，且共享内存更简单
- 选择 `requests.Session()`：自动处理连接池，性能提升约 20%
- 最大线程数设置为源数量：避免过多线程造成资源浪费

**性能与可靠性**：

- 时间复杂度：从 O(n) 降至 O(1)（相对于源数量）
- 空间复杂度：无明显变化，每个线程独立处理
- 瓶颈：最慢的规则源决定总耗时
- 缓解策略：保留超时设置和重试机制

**避免技术债务**：

- 复用现有的 `fetch_single_rule()` 方法，仅修改调用方式
- 保持与现有元数据格式的兼容性

### 2. GitHub Actions 稳定性增强

**策略**：添加失败通知、改进错误处理、避免 Git 冲突

**高层策略**：
改进 `daily-update.yml` Workflow，添加失败通知机制，使用 `continue-on-error` 让单个源失败不影响整体，在推送前先拉取最新代码。

**工作原理**：

- 添加 `if: failure()` 条件的步骤，在失败时自动创建 GitHub Issue
- 为下载步骤添加 `continue-on-error: true`，失败时不立即终止 Workflow
- 在 `git push` 前添加 `git pull --rebase` 避免冲突
- 删除冗余的 `jekyll-gh-pages.yml`（项目中无 Jekyll 源文件）

**关键决策理由**：

- 使用 GitHub Issue 作为通知机制：无需外部服务，简单有效
- 使用 `continue-on-error`：单个源失败不应阻止其他源的更新
- 使用 `git pull --rebase`：避免自动提交时的冲突

**性能与可靠性**：

- 无性能影响
- 显著提高稳定性：避免单点故障导致整个 Workflow 失败

### 3. 代码 Bug 修复

**策略**：修复正则匹配误判、更新配置错误

**高层策略**：
修改 `merge_rules.py` 第 141 行的正则匹配逻辑，增强准确性；更新 `config/default.header` 中的描述文本。

**工作原理**：

- 修改正则匹配模式，要求规则以 `/` 开头且不包含空格（真正的正则规则特征）
- 更新 `default.header` 第 9 行的描述从 "Adguard this is the perfect filter" 改为项目相关描述
- 固定 `requirements.txt` 中的 `requests` 版本为 `>=2.28.0,<3.0.0`

**关键决策理由**：

- 增强正则匹配：避免将普通规则（如 `//comments`）误判为正则
- 固定版本：避免未来不兼容版本导致的问题

### 4. 日志记录改进

**策略**：使用 Python `logging` 模块替代 print 语句

**高层策略**：
在 `scripts/fetch_rules.py` 和 `scripts/merge_rules.py` 中添加 logging 配置，将日志保存到 `logs/` 目录。

**工作原理**：

- 配置 `logging` 模块，同时输出到控制台和文件
- 日志文件按日期命名（如 `fetch_20260613.log`）
- 保留控制台输出用于 GitHub Actions 日志查看
- 日志级别：INFO 及以上

**关键决策理由**：

- 使用 `logging` 而非 print：更灵活，支持分级、格式化、持久化
- 按日期命名日志文件：便于回溯问题

### 5. 添加单元测试

**策略**：使用 `pytest` 测试核心逻辑

**高层策略**：
创建 `tests/` 目录，编写测试用例覆盖规则解析、去重、分类逻辑。

**工作原理**：

- 测试 `process_rule()` 方法的各种规则类型识别
- 测试正则匹配误判场景
- 测试去重逻辑
- 测试边界情况（空文件、编码问题等）

**关键决策理由**：

- 使用 `pytest`：简单易用，与 Python 生态良好集成
- 测试核心逻辑：确保重构时不破坏现有功能

## 实施注意事项

- **性能**：并发下载时注意不要触发源服务器的速率限制（当前 4 个源，风险较低）
- **日志**：避免记录敏感信息（URL 中可能的认证信息）
- **向后兼容性**：确保所有修改不影响现有功能（元数据格式、输出格式）
- **爆炸半径控制**：优先修改受影响最小的部分，逐步推进；使用特性分支测试

## 架构设计

由于这是一个脚本项目的优化，不涉及复杂的架构变更。主要改动在：

1. `scripts/fetch_rules.py` - 添加并发下载逻辑和 logging
2. `scripts/merge_rules.py` - 修复 bug 和添加 logging
3. `.github/workflows/` - 改进 CI/CD 流程
4. `config/` - 更新配置
5. `requirements.txt` - 固定版本
6. `tests/` - 新增测试目录

### 系统架构图

由于改动较小，不需要复杂的架构图。数据流保持不变：

```
规则源 → fetch_rules.py (并发下载) → rules/ → merge_rules.py (合并去重) → dist/
```

## 目录结构

```
project-root/
├── scripts/
│   ├── fetch_rules.py  # [MODIFY] 添加并发下载逻辑，使用 ThreadPoolExecutor 和 Session
│   └── merge_rules.py  # [MODIFY] 修复正则匹配 bug（第 141 行），添加 logging
├── config/
│   ├── sources.json    # [KEEP] 无改动
│   └── default.header  # [MODIFY] 更新第 9 行描述文本
├── .github/
│   └── workflows/
│       ├── daily-update.yml      # [MODIFY] 添加失败通知、continue-on-error、git pull --rebase
│       ├── weekly-release.yml    # [KEEP] 无改动
│       └── jekyll-gh-pages.yml   # [DELETE] 删除冗余 Workflow（项目中无 Jekyll 源文件）
├── tests/            # [NEW] 添加单元测试目录
│   ├── __init__.py
│   ├── test_fetch_rules.py  # [NEW] 测试 fetch_rules.py 的核心逻辑
│   └── test_merge_rules.py  # [NEW] 测试 merge_rules.py 的规则解析和去重
├── logs/             # [NEW] 日志目录（gitignore）
└── requirements.txt  # [MODIFY] 固定 requests 版本为 >=2.28.0,<3.0.0，添加 pytest
```

## 关键代码结构（可选）

由于改动主要涉及现有函数的修改，而非新接口设计，此处不提供代码快照。关键修改点：

1. **fetch_rules.py** - `fetch_all_rules()` 方法：

- 创建 `ThreadPoolExecutor`
- 使用 `executor.submit()` 提交任务
- 使用 `as_completed()` 收集结果

2. **merge_rules.py** - `process_rule()` 方法：

- 修改第 141 行的正则匹配模式
- 增强对真正正则规则的检查

3. **daily-update.yml** - 新增步骤：

- 使用 `actions/github-script` 创建失败通知 Issue