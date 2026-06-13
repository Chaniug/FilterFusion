---
name: 修复 checksum 生成方式
overview: 将 FilterFusion 的 checksum 生成方式从 SHA-256 改为 ABP 标准规范（MD5 + Base64），使生成的规则文件完全兼容广告拦截器。
todos:
  - id: add-base64-import
    content: 在 scripts/merge_rules.py 中新增 import base64
    status: completed
  - id: modify-checksum-logic
    content: 修改 merge_rules.py 中 checksum 计算逻辑为 MD5 + Base64 格式
    status: completed
    dependencies:
      - add-base64-import
  - id: update-print-statement
    content: 更新 merge_rules.py 中 checksum 打印语句，完整显示 24 字符
    status: completed
    dependencies:
      - modify-checksum-logic
  - id: update-docs
    content: 更新 PROJECT_DOCS.md 中 CHECKSUM 说明为 ABP 标准格式
    status: completed
  - id: verify-checksum
    content: 运行合并脚本验证新 checksum 格式正确生成
    status: completed
    dependencies:
      - modify-checksum-logic
      - update-print-statement
---

## 用户需求

将 FilterFusion 规则文件的 checksum 生成方式从当前的 SHA-256（64 字符十六进制）改为符合 Adblock Plus 标准规范的 MD5 + Base64 格式（24 字符），以提高兼容性并缩短长度。

## 功能内容

- 修改 `scripts/merge_rules.py` 中的 checksum 计算逻辑，使用 MD5 哈希 + Base64 编码
- 更新项目文档中关于 checksum 格式的描述
- 确保生成的 checksum 完全符合 ABP 规范，兼容 uBlock Origin、AdGuard 等广告拦截器

## 视觉效果

无 UI 变更，仅影响生成的规则文件头部 `! Checksum:` 字段内容，从 64 字符缩短为 24 字符。

## 技术栈

- Python 3（已有）
- `hashlib`（已有，用于 MD5）
- `base64`（需新增导入）

## 实现方案

### 修改策略

采用标准 ABP checksum 算法：

1. 将完整文件内容（含 `{CHECKSUM}` 占位符）去除 `! Checksum:` 行
2. 对剩余内容计算 MD5 哈希（二进制）
3. 对 MD5 结果进行 Base64 编码
4. 将结果替换回 `{CHECKSUM}` 占位符

### 关键代码修改

**文件：`scripts/merge_rules.py`**

1. **新增导入**（第 1-9 行区域）：
在导入区域添加 `import base64`

2. **修改 checksum 计算逻辑**（原第 288-289 行）：

```python
# 计算校验和（ABP 标准：MD5 + Base64）
content_for_checksum = "\n".join(
line for line in content.split("\n")
if not line.startswith("! Checksum:")
)
md5_hash = hashlib.md5(content_for_checksum.encode('utf-8')).digest()
checksum = base64.b64encode(md5_hash).decode('utf-8')
content = content.replace('{CHECKSUM}', checksum)
```

3. **更新打印语句**（原第 317 行）：
由于 checksum 现在只有 24 字符，无需截断显示，改为：

```python
print(f"🔐 校验和: {checksum}")
```

**文件：`PROJECT_DOCS.md`**

4. **更新文档说明**（第 208 行）：
将 `{CHECKSUM}` 的说明从"完整文件的 SHA256 校验和"改为"MD5 + Base64 校验和（ABP 标准格式）"

## 架构设计

本次修改为局部逻辑优化，不影响整体架构。仅涉及 checksum 生成算法的替换，不改变数据流和其他处理逻辑。

## 目录结构

本次修改涉及以下文件：

```
d:\FilterFusion\
├── scripts/
│   └── merge_rules.py  [MODIFY] 修改 checksum 生成逻辑，新增 base64 导入，更新打印语句
└── PROJECT_DOCS.md     [MODIFY] 更新 CHECKSUM 占位符说明文档
```

## 注意事项

- ABP checksum 计算时必须排除 `! Checksum:` 行本身，否则会导致校验失败
- Base64 编码结果为 24 字符（16 字节 MD5 → Base64 补位后 24 字符）
- 修改后需运行一次合并脚本验证生成的 checksum 格式正确