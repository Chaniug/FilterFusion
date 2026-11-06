"""产物完整性校验 — 只读检查 dist/ 输出，不改变任何文件路径或内容。

设计原则（重要）：
- 纯标准库、无网络、无写操作，可在 CI 与本地安全重复运行。
- 只检查「数据损坏」级别的问题，正常产物必然通过；刻意 **不校验时间戳**，
  因为 GitHub 定时任务常有数小时排队延迟，日期判断会制造假失败。
- 不参与规则生成，dist/ 路径仍由各合并脚本自行推导，本模块只读取。

用法：python -m scripts.validate_dist
退出码：0 = 全部通过；1 = 发现异常（问题清单打印到 stdout）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 与 merge_rules.py / merge_dns_rules.py 的 dist_dir 推导方式保持一致（只读）
DIST_DIR: Path = Path(__file__).resolve().parent.parent / "dist"

ADBLOCK_FILES: tuple[str, ...] = ("adblock-mo.txt", "adblock-pc.txt")
DNS_FILES: tuple[str, ...] = ("dns-blocklist.txt",)
CORE_FILES: tuple[str, ...] = ADBLOCK_FILES + DNS_FILES

# 当前产物为 4~7 MB / 数十万行。1000 条只为抓「抓取全失败但旧文件残留」
# 或「合并输出被截断」这类事故，正常规则量级距离下限有 2 个数量级余量。
MIN_RULE_COUNT: int = 1000

_VERSION_RE: re.Pattern[str] = re.compile(r"^! Version: (\d{12})\s*$", re.MULTILINE)
# AdGuard 规范要求无 padding 的 Base64：带 '=' 会被判为 invalid checksum
_CHECKSUM_RE: re.Pattern[str] = re.compile(r"^! Checksum: ([A-Za-z0-9+/]+)\s*$", re.MULTILINE)
_PLACEHOLDER_RE: re.Pattern[str] = re.compile(r"\{[A-Z][A-Z_]*\}")


def is_rule_line(line: str) -> bool:
    """是否是一条有效规则（排除注释、ABP 格式声明与空行）。"""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(("!", "["))


def validate_file(path: Path, *, adblock: bool, min_rules: int = MIN_RULE_COUNT) -> tuple[list[str], int]:
    """校验单个产物文件，返回 (问题列表, 有效规则数)。

    问题列表为空即通过。只读取文件，绝不修改。
    """
    if not path.is_file():
        return [f"文件不存在: {path.name}"], 0

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [f"无法读取 {path.name}: {e}"], 0

    if not content.strip():
        return [f"{path.name}: 文件为空"], 0

    errors: list[str] = []
    lines = content.splitlines()

    # 头部字段（只看前 30 行，避免规则正文里的花括号造成误报）
    head = "\n".join(lines[:30])
    if not _VERSION_RE.search(head):
        errors.append(f"{path.name}: 缺少有效的 ! Version 头部（应为 12 位 YYYYMMDDHHMM）")
    leftover = sorted(set(_PLACEHOLDER_RE.findall(head)))
    if leftover:
        errors.append(f"{path.name}: 头部存在未替换的占位符 {leftover[:3]}")

    if adblock:
        if not lines[0].strip() == "[Adblock Plus 2.0]":
            errors.append(f"{path.name}: 首行缺少 [Adblock Plus 2.0] 声明")
        checksum = _CHECKSUM_RE.search(head)
        if not checksum:
            errors.append(f"{path.name}: 缺少有效 ! Checksum（须为无 padding 的 Base64）")
        if any(not line.strip() for line in lines):
            # AdGuard 的 TS / Rust 两种 checksum 实现对空行处理不同，
            # 文件含空行会被其中一种引擎判为 invalid checksum。
            errors.append(f"{path.name}: 存在空行，会破坏 AdGuard checksum 一致性")

    rule_count = sum(1 for line in lines if is_rule_line(line))
    if rule_count < min_rules:
        errors.append(f"{path.name}: 有效规则仅 {rule_count} 条（下限 {min_rules}），疑似抓取或合并失败")

    return errors, rule_count


def main() -> int:
    all_errors: list[str] = []
    for name in CORE_FILES:
        problems, count = validate_file(DIST_DIR / name, adblock=name in ADBLOCK_FILES)
        if problems:
            all_errors.extend(problems)
            for problem in problems:
                print(f"❌ {problem}")
        else:
            print(f"✅ {name}: {count:,} 条规则")

    if all_errors:
        print(f"\n❌ 产物完整性校验失败（{len(all_errors)} 项），已阻止部署")
        return 1

    print("\n✅ 产物完整性校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
