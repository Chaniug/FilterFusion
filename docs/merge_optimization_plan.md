# FilterFusion 全局优化方案

> 分析日期: 2026-06-16 | 原则：仅优化内部逻辑，不改变输出产物

---

## 概览

```
Phase 1: merge_rules.py 核心性能优化  (4 项必做 + 1 项可选)
Phase 2: GitHub Actions 工作流优化    (3 项必做)
Phase 3: 辅助脚本清理                 (3 项必做)
─────────────────────────────────────────
共 11 项，涉及 4 个文件，输出产物不变，无新依赖
```

| 阶段 | 文件 | 改动数 | 影响范围 |
|------|------|--------|----------|
| Phase 1 | `scripts/merge_rules.py` | 4~5 | CPU / 内存 |
| Phase 2 | `.github/workflows/*.yml` | 3 | CI 速度 / 稳定性 |
| Phase 3 | `scripts/*.py` | 3 | 代码整洁度 |

---

# Phase 1 — merge_rules.py 核心性能优化

---

## 🔴 高影响 / 低改动成本

### 1.1 去重键 `f"{typ}:{rule}"` 中的 `typ` 前缀冗余

`process_rule()` 对相同文本的规则分类是**确定性**的（纯文本模式匹配），同一条规则不可能在不同源中被分到不同类型。因此 `typ:` 前缀完全冗余。

```python
# 当前：每次拼接字符串，且 hash 时要遍历更长字符串
rule_id = f"{typ}:{rule}"

# 建议：直接用 rule 作为去重键
rule_id = rule
```

共三处：源内去重、源内计数、全局去重。

**收益**：省去每次规则处理的字符串拼接开销，set 内存占用略有下降。**风险：无**。

### 1.2 每条规则都做 `unicodedata.normalize('NFKC', ...)` — 多数是纯 ASCII

NFKC 标准化是 CPU 密集操作。广告过滤规则绝大多数是纯 ASCII（URL、CSS 选择器、英文注释），Unicode 字符极少见。

```python
# 当前
rule = unicodedata.normalize('NFKC', line.strip())
if not rule:
    return (None, None)

# 建议：加 ASCII 快速路径
rule = line.strip()
if not rule:
    return (None, None)
if not rule.isascii():          # Python 3.7+，O(n) 但极快
    rule = unicodedata.normalize('NFKC', rule)
```

**收益**：对 2 万条规则的文件，若 99% 是 ASCII，可跳过 99% 的 NFKC 调用。**风险：极低**。

---

## 🟡 中影响 / 中改动成本

### 1.3 `html_filter_keywords` 的 `any(... in rule)` 扫描效率低

当前对每条规则遍历最多 12 个关键词做子串搜索，每个关键词都触发一次 `str.__contains__`。

```python
# 当前：每条规则最多 12 次子串扫描
if any(k in rule for k in html_filter_keywords):
    ...

# 建议：类级别预编译一个正则，单次扫描
class RuleMerger:
    _HTML_FILTER_RE = re.compile(
        r'#%#|#@%#|#\$#|#@\$#|#\?#|#@\?#|'
        r'#\+js\(|#@#\+js\(|\$removeparam|\$cookie=|\$redirect=|\$generichide|'
        r'scriptlet\(|jsinject'
    )
    # 使用时：
    if self._HTML_FILTER_RE.search(rule):
        return ('html_filter', rule)
```

`html_filter_keywords` 列表可删除（正则已覆盖全部）。

**收益**：单次扫描替代多次扫描，且正则引擎在 C 层执行，对大量规则效果明显。**风险：低**。

### 1.4 正则规则检测的启发式 `len(pattern) > 15` 不够精确

当前逻辑中 `len(pattern) > 15` 是为了兜底那些不含明显正则字符但确实是正则的规则，但这也可能把长 URL 规则误判为正则。

```python
# 当前
if has_regex_chars or len(pattern) > 15:

# 建议：去掉 len > 15 兜底
if has_regex_chars:
```

**收益**：降低误分类率，避免普通规则被错误放入正则分组。**风险：低-中**（少数不含正则特殊字符的长规则可能从 `regex` 变为其他分类，但规则不会丢失）。

---

## 🟢 低影响 / 可选优化

### 1.5（可选）规则双重存储：`seen_rules` + `groups[typ]` 各存一份

同一条规则文本同时存在于 `seen_rules`（Set）和 `groups[typ]`（Set）中。考虑到 AdBlock 规则通常 2~5 万条，Python 字符串有 interning 优化，实际额外内存约几十 MB，优先级不高，**本期不做**。

### 1.6（可选）合并阶段可并行处理多个源文件

可用 `ThreadPoolExecutor` 并行读取和分类，但对于 4 个源、总计几万条规则的规模，串行已足够快，不建议增加复杂度，**本期不做**。

---

# Phase 2 — GitHub Actions 工作流优化

---

### 2.1 `daily-update.yml`：`fetch-depth: 0` → `fetch-depth: 1`

- **文件**：`.github/workflows/daily-update.yml`
- **现状**：`actions/checkout@v6` 使用 `fetch-depth: 0`，拉取完整 Git 历史
- **改动**：改为 `fetch-depth: 1`（仅最新 commit）

```yaml
# 当前
- uses: actions/checkout@v6
  with:
    fetch-depth: 0  # 获取完整历史，便于 rebase

# 建议
- uses: actions/checkout@v6
  with:
    fetch-depth: 1
```

**收益**：每次 CI 节省数十秒 clone 时间，随仓库历史增长收益递增。当前 job 的 rebase 策略无需完整历史。**风险：无**。

### 2.2 `weekly-release.yml`：`fetch-depth: 0` → `fetch-depth: 1`

- **文件**：`.github/workflows/weekly-release.yml`
- **同上**：周度 job 只需最新 commit 即可创建 tag，无需完整历史

**收益**：同上。**风险：无**。

### 2.3 `daily-update.yml`：添加 `concurrency` 控制

- **文件**：`.github/workflows/daily-update.yml`
- **现状**：无并发控制。若定时触发（UTC 00:00）和手动触发（`workflow_dispatch`）同时运行，两个 job 会争抢 `git push`

```yaml
# 在 on: 块同级添加
concurrency:
  group: daily-update
  cancel-in-progress: false
```

**收益**：消除竞态条件，大幅提升自动化稳定性。**风险：无**。

---

# Phase 3 — 辅助脚本清理

---

### 3.1 `merge_rules.py`：`groups['comment']` 无用填充

- **文件**：`scripts/merge_rules.py`，方法 `collect_and_process_rules`
- **现状**：注释规则被收集到 `groups['comment']` Set（最多 10 条），但输出阶段完全跳过此分组
- **改动**：跳过存储，仅保留计数器（或直接不处理 comment）

**收益**：避免无用的内存分配和 set 操作。**风险：无**。

### 3.2 `merge_rules.py`：移除 `_ = f.write(content)` 多余赋值

- **文件**：`scripts/merge_rules.py`，方法 `merge`
- **现状**：`_ = f.write(content)` 用下划线捕获返回值
- **原因**：`pyproject.toml` 已配置 `reportUnusedCallResult = "none"`，此模式不再必要

**收益**：代码整洁。**风险：无**。

### 3.3 `fetch_rules.py`：清理不可达 `raise RuntimeError`

- **文件**：`scripts/fetch_rules.py`，方法 `fetch_single_rule`
- **现状**：方法底部有 `raise RuntimeError("Unreachable code...")`，仅用于帮助类型推断
- **改动**：重构为无死代码的清晰控制流

**收益**：消除死代码，减少误导。**风险：无**。

---

## 📊 执行计划

| 顺序 | 阶段 | 改动 | 依赖 | 预估影响 |
|------|------|------|------|----------|
| 1 | Phase 1 | 1.1 去重键优化 | 无 | CPU↓ 内存↓ |
| 2 | Phase 1 | 1.2 ASCII 快速路径 | 无 | CPU↓ |
| 3 | Phase 1 | 1.3 预编译正则 | 无 | CPU↓ |
| 4 | Phase 1 | 1.4 收紧正则检测 | 无 | 分类精度↑ |
| 5 | Phase 2 | 2.1 daily fetch-depth | 无 | CI 速度↑ |
| 6 | Phase 2 | 2.2 weekly fetch-depth | 无 | CI 速度↑ |
| 7 | Phase 2 | 2.3 concurrency 控制 | 无 | 稳定性↑ |
| 8 | Phase 3 | 3.1 comment 清理 | 无 | 内存↓ |
| 9 | Phase 3 | 3.2 移除多余赋值 | 无 | 整洁度↑ |
| 10 | Phase 3 | 3.3 死代码清理 | 无 | 整洁度↑ |

> Phase 1 / Phase 2 / Phase 3 之间互不依赖，可并行实施。

---

## ✅ 验证清单

- [ ] `python -m scripts.fetch_rules && python -m scripts.merge_rules` 无报错
- [ ] 优化前后 `dist/adblock-main.txt` 行数与规则顺序一致
- [ ] 非 ASCII 规则（如中文注释）NFKC 路径仍正常
- [ ] GitHub Actions `daily-update` workflow_dispatch 触发成功
- [ ] `weekly-release` workflow_dispatch 触发成功
- [ ] 同时触发两次 `daily-update`，concurrency 生效（后一个排队）
- [ ] `config/summary.json` 统计数字正确
