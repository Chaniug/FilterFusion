# 常见问题 FAQ

## 使用问题

### Q1：规则订阅后不生效？

**可能原因**：

1. **订阅地址填错** — 确认地址以 `https://` 开头，且能浏览器直接访问
2. **工具不支持 ABP 格式** — 确认工具支持 Adblock Plus 2.0 格式
3. **规则未更新** — 手动点击"更新过滤器"按钮
4. **广告在白名单** — 检查工具的白名单设置

**解决步骤**：

```
1. 浏览器访问订阅地址，确认能返回规则文本
2. 在广告拦截工具中删除旧订阅，重新添加
3. 手动触发"更新过滤器"
```

### Q2：如何新增我自己的规则源？

编辑 `config/sources.yaml`，在 `sources:` 段新增一项：

```yaml
  # 我的规则说明
  - name: 我的规则名
    category: mo          # mo=手机端 / pc=电脑端 / bo=两端共用
    url: https://我的规则地址
    id: x1                # 不能与已有 id 重复
```

然后运行：

```bash
python -m scripts.fetch_rules
python -m scripts.merge_all
```

### Q3：GitHub Actions 每天自动运行吗？

是的。`daily-update.yaml` 使用 `cron` 表达式每天自动触发。

如果需要修改运行时间，编辑 `.github/workflows/daily-update.yaml` 的 `cron` 字段：

```yaml
schedule:
  - cron: '0 0 * * *'  # 每天 UTC 0:00（北京时间 8:00）
```

### Q4：为什么我的规则文件没有生成？

**排查步骤**：

1. 检查 `config/sources.yaml` 中的 `custom_rules` 段是否正确
2. 确认 `sources` 中引用的 id 都在上方的 `sources:` 段中定义
3. 运行合并脚本时查看终端输出，是否有报错信息
4. 检查 `fetch_meta.json`（临时目录）中的抓取结果

### Q5：如何只生成手机端规则？

修改 `config/sources.yaml` 的 `custom_rules` 段，只保留手机端相关的 id：

```yaml
custom_rules:
  - output: adblock-mo.txt
    sources: [m1, m2, m3, b1, b2]  # 只含手机端和共用源
```

或者注释掉电脑端的组合规则。

### Q6：规则文件太大，影响性能吗？

规则文件大小对性能的影响微乎其微：

- **内存占用** — uBlock Origin 等工具使用高效的数据结构，规则数不是线性影响
- **匹配速度** — 基于哈希表，O(1) 查找
- **网络流量** — 规则文件只下载一次，后续增量更新

如果仍担心，可以使用自定义组合规则生成精简版。

## 配置问题

### Q7：`config/sources.yaml` 报语法错误？

**常见原因**：

1. **Tab 缩进** — YAML 不允许 Tab，必须用空格
2. **冒号后缺空格** — `name:值` ❌，`name: 值` ✅
3. **大小写错误** — `category: Mo` ❌（大小写敏感），`category: mo` ✅
4. **URL 未加引号** — 如果 URL 含 `#` 等特殊字符，需用引号包裹

**验证方法**：

```bash
# 使用 Python 验证 YAML 语法
python -c "import yaml; yaml.safe_load(open('config/sources.yaml'))"
```

### Q8：`category` 填 `mobile` 还是 `mo`？

两个都可以！

- `mo` — 缩写（推荐，少打字）
- `mobile` — 旧全称（兼容，向后兼容）

脚本会自动映射为内部全称，无差别。

### Q9：如何禁用某个规则源？

将整个源项用 `#` 注释掉：

```yaml
  # - name: 不需要的源
  #   category: mo
  #   url: https://example.com/filter.txt
  #   id: m2
```

或者删除该项（注释更安全，方便日后恢复）。

## 开发者问题

### Q10：如何本地运行测试？

```bash
# 克隆项目
git clone https://github.com/Chaniug/FilterFusion.git
cd FilterFusion

# 安装依赖
pip install -r requirements.txt

# 抓取规则
python -m scripts.fetch_all

# 合并规则
python -m scripts.merge_all

# 查看生成的规则
ls dist/
```

### Q11：如何贡献代码？

1. Fork 本项目
2. 创建特性分支（`git checkout -b feature/xxx`）
3. 提交改动（`git commit -m 'Add xxx'`）
4. 推送到 Fork（`git push origin feature/xxx`）
5. 创建 Pull Request

### Q12：Python 版本要求为什么是 3.14+？

FilterFusion 要求 Python 3.14+ 作为最低运行版本（CI 锁定 3.14 以保证构建可重现性），
代码中实际采用的现代语法特性如下（均为 3.7–3.12 既有特性，非 3.14 专属）：

- `from __future__ import annotations`（3.7+，延迟类型求值）
- 内置泛型注解 `list[dict[str, Any]]` / `dict[str, set[str]]`（3.9+）
- `X | Y` 联合类型（3.10+）
- `StrEnum`（3.11，类型安全且 JSON 友好的枚举）
- `datetime.UTC`（3.11，替代 `datetime.utcnow()`）
- `type` 语句类型别名（3.12，PEP 695）

这些特性能提升代码质量与可读性；Python 3.14 本身主要是性能与稳健性改进，
并未引入需要代码主动采用的新语法，因此将最低版本设为 3.14 主要是为了统一运行环境，
而非语法上的硬依赖。

## 下一步

- 了解完整配置方法 → [配置说明](/wiki/配置说明)
- 学习自定义规则组合 → [自定义组合规则](/wiki/自定义组合规则)
