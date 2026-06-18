"""FilterFusion 规则合并模块 — 分类、去重、输出标准 ABP 格式。"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class RuleType(StrEnum):
    """规则语义分类（符合 AdGuard/ABP/uBlock 标准）。"""

    COMMENT = "comment"
    EXCEPTION = "exception"
    REGEX = "regex"
    HTML_FILTER = "html_filter"
    ELEMENT_HIDE = "element_hide"
    SPECIAL = "special"
    NORMAL = "normal"


class _SafeDict(dict[str, str]):
    """format_map 专用字典：缺失的占位符保持原样（用于 {CHECKSUM} 延后填充）。"""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class RuleMerger:
    """规则合并器：读取抓取产物 → 分类去重 → 输出标准格式。

    热路径 process_rule() 使用类级预编译正则常量，避免每次调用重建数据结构。
    """

    __slots__ = (
        "project_root",
        "dist_dir",
        "rules_dir",
        "initial_rule_count",
        "final_rule_count",
        "start_time",
    )

    # AdGuard/uBlock 扩展语法（必须在元素隐藏之前判断）
    _HTML_FILTER_RE = re.compile(
        r"#%#|#@%#|#\$#|#@\$#|#\?#|#@\?#|"
        r"#\+js\(|#@#\+js\(|\$removeparam|\$cookie=|\$redirect=|\$generichide|"
        r"scriptlet\(|jsinject"
    )

    # 特殊参数关键词：单次正则扫描替代 8 次 any(in) 子串搜索
    _SPECIAL_RE = re.compile(
        r"badfilter|important|app=|domain=|csp=|replace=|popup|third-party"
    )

    # 正则特殊字符：单次字符类扫描替代 14 次 any(in) 搜索
    _REGEX_CHAR_RE = re.compile(r"[.*+?\\\[\](){}^$|]")

    def __init__(self) -> None:
        self.project_root: Path = Path(__file__).resolve().parent.parent
        print(f"项目根目录: {self.project_root}")

        self.dist_dir: Path = self.project_root / "dist"
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir: Path = self.project_root / "rules"

        print(f"分发目录: {self.dist_dir}")
        print(f"规则目录: {self.rules_dir}")

        # 统计信息
        self.initial_rule_count: int = 0
        self.final_rule_count: int = 0
        self.start_time: datetime = datetime.now()

    def load_metadata(self) -> dict[str, Any]:
        meta_path = self.rules_dir / "fetch_meta.json"
        print(f"尝试加载元数据: {meta_path}")

        if not meta_path.exists():
            print(f"❌ 错误：找不到抓取元数据文件 {meta_path}")
            sys.exit(1)

        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            print("成功加载元数据文件")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ 错误：元数据文件格式不正确 {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 加载元数据时出错: {e}")
            sys.exit(1)

    def load_header_template(self) -> str:
        header_path = self.project_root / "config" / "default.header"
        print(f"尝试加载头部模板: {header_path}")

        if not header_path.exists():
            print(f"❌ 错误：找不到头部模板 {header_path}")
            print("请确保文件存在:")
            print(f"位置: {header_path}")
            print("文件内容应为:")
            print("-" * 50)
            print(
                "! Title: FilterFusion AdBlock Rules\n"
                "! Version: {VERSION}\n"
                "! Updated: {TIMEUPDATED}\n"
                "! Last modified: {TIMEUPDATED}\n"
                "! Checksum: {CHECKSUM}\n"
                "! Homepage: {HOMEPAGE}\n"
                "! Expires: 1 day\n"
                "! License: {LICENSE}"
            )
            print("-" * 50)
            sys.exit(1)

        try:
            return header_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"❌ 读取头部模板失败: {e}")
            sys.exit(1)

    def generate_source_list(self, sources: list[dict[str, Any]]) -> str:
        """生成格式化的源列表信息。"""
        source_info: list[str] = []
        for source in sources:
            status = source.get("status", "unknown")
            if status == "success":
                status_icon = "✓"
                ts = source.get("timestamp", "")
                update_info = f" (更新: {ts[:10]})" if ts else ""
            elif status == "disabled":
                status_icon = "-"
                update_info = " (已禁用)"
            else:
                status_icon = "✗"
                update_info = ""
            source_info.append(f"! - {status_icon} {source['name']}{update_info}")
        return "\n".join(source_info)

    def process_rule(self, line: str) -> tuple[RuleType | None, str | None]:
        """对单条规则进行规范化、分组和兼容性处理，返回 (type, rule)。

        规则分类优先级（符合 AdGuard/ABP/uBlock 标准）:
        1. 注释 (! 或 [Adblock Plus])
        2. 例外规则 (@@)
        3. 正则规则 (/pattern/flags)
        4. HTML/脚本注入规则 (#%#, #$#, scriptlet 等)
        5. 元素隐藏规则 (##, #@#)
        6. 特殊参数规则 ($badfilter, $important 等)
        7. 普通屏蔽规则
        """
        # 去除不可见字符和多余空白
        rule = line.strip()
        if not rule:
            return (None, None)
        # ASCII 快速路径：99%+ 规则为纯 ASCII，跳过 NFKC 规范化
        if not rule.isascii():
            rule = unicodedata.normalize("NFKC", rule)

        # 1. 注释规则（排除 ##, #@#, #%#, #$#, #?#, #+# 等规则指令）
        if rule.startswith("!") or rule.startswith("["):
            return (RuleType.COMMENT, rule)

        # 2. 例外规则 (@@) - 最高优先级（例外规则可能包含其他语法）
        if rule.startswith("@@"):
            return (RuleType.EXCEPTION, rule)

        # 3. 正则规则 (Adblock Plus 格式: /pattern/flags)
        # 标准: 以 / 开头，以 / 结尾，中间是正则模式，尾部可有标志 (i, g, m)
        if rule.startswith("/") and not rule.startswith("//"):
            last_slash = rule.rfind("/")
            if last_slash > 0:
                flags = rule[last_slash + 1 :]
                if all(c in "igm" for c in flags) or not flags:
                    pattern = rule[1:last_slash]
                    # 类级预编译正则单次扫描，替代 14 次 any(in)
                    if self._REGEX_CHAR_RE.search(pattern):
                        return (RuleType.REGEX, rule)

        # 4. AdGuard/uBlock 扩展语法（必须在元素隐藏之前判断）
        if self._HTML_FILTER_RE.search(rule):
            return (RuleType.HTML_FILTER, rule)

        # 5. 元素隐藏规则
        if "##" in rule:
            return (RuleType.ELEMENT_HIDE, rule)

        # 6. 特殊参数规则（限定在选项部分：$ 之后）
        if "$" in rule:
            option_part = rule.split("$", 1)[1]
            # 类级预编译正则单次扫描，替代 8 次 any(in)
            if self._SPECIAL_RE.search(option_part):
                return (RuleType.SPECIAL, rule)

        # 7. 普通屏蔽规则
        return (RuleType.NORMAL, rule)

    def collect_and_process_rules(
        self, sources: list[dict[str, Any]]
    ) -> tuple[list[str], dict[str, set[str]], list[dict[str, Any]]]:
        """收集并处理规则：语法分组、格式规范、扩展兼容，同时统计每个源的规则数。"""
        # 分组容器（comment 不存储，仅跳过）
        groups: dict[str, set[str]] = {
            RuleType.NORMAL: set(),
            RuleType.EXCEPTION: set(),
            RuleType.ELEMENT_HIDE: set(),
            RuleType.HTML_FILTER: set(),
            RuleType.REGEX: set(),
            RuleType.SPECIAL: set(),
        }
        seen_rules: set[str] = set()
        source_stats: list[dict[str, Any]] = []

        print("收集和处理规则:")
        for source in sources:
            if source.get("status") != "success":
                continue
            source_path = self.rules_dir / source["file"]
            print(f"处理源文件: {source_path}")
            if not source_path.exists():
                continue

            source_rule_count = 0
            source_seen: set[str] = set()  # 源内去重（独立于全局）
            try:
                with open(source_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        typ, rule = self.process_rule(line)
                        if not typ or not rule:
                            continue
                        # 跳过注释
                        if typ == RuleType.COMMENT:
                            continue
                        # 源内去重计数
                        if rule in source_seen:
                            continue
                        source_seen.add(rule)
                        source_rule_count += 1
                        # 全局去重
                        if rule in seen_rules:
                            continue
                        seen_rules.add(rule)
                        groups[typ].add(rule)
            except Exception as e:
                print(f"⚠️ 警告：处理 {source['name']} 规则时出错: {e}")
            print(f"源 {source['name']} 有效规则数: {source_rule_count}")
            source_stats.append({"name": source["name"], "rule_count": source_rule_count})

        # 按分组分类拼接输出
        merged_lines: list[str] = []
        if groups[RuleType.EXCEPTION]:
            merged_lines.append("! === 例外规则 Exception Rules ===")
            merged_lines.extend(sorted(groups[RuleType.EXCEPTION]))
            merged_lines.append("")
        if groups[RuleType.ELEMENT_HIDE]:
            merged_lines.append("! === 元素隐藏规则 Element Hiding Rules ===")
            merged_lines.extend(sorted(groups[RuleType.ELEMENT_HIDE]))
            merged_lines.append("")
        if groups[RuleType.HTML_FILTER]:
            merged_lines.append("! === AdGuard/HTML Scriptlet Rules ===")
            merged_lines.extend(sorted(groups[RuleType.HTML_FILTER]))
            merged_lines.append("")
        if groups[RuleType.REGEX]:
            merged_lines.append("! === 正则规则 Regex Rules ===")
            merged_lines.extend(sorted(groups[RuleType.REGEX]))
            merged_lines.append("")
        if groups[RuleType.SPECIAL]:
            merged_lines.append("! === 特殊参数/实验性规则 Special/Experimental ===")
            merged_lines.extend(sorted(groups[RuleType.SPECIAL]))
            merged_lines.append("")
        if groups[RuleType.NORMAL]:
            merged_lines.append("! === 屏蔽规则 Blocking Rules ===")
            merged_lines.extend(sorted(groups[RuleType.NORMAL]))
            merged_lines.append("")

        total = sum(len(v) for v in groups.values())
        print(f"收集了 {total} 条唯一规则")
        return merged_lines, groups, source_stats

    @staticmethod
    def generate_version() -> str:
        """生成简单的语义化版本号（YYYYMMDD）。"""
        today = datetime.now(UTC)
        return f"{today.year}{today.month:02d}{today.day:02d}"

    def merge(self) -> None:
        print("=" * 50)
        print("🔧 FilterFusion - 广告规则合并工具")
        print("=" * 50)

        # 步骤1: 加载元数据
        print("步骤1: 加载元数据")
        metadata = self.load_metadata()
        sources = metadata["sources"]

        # 检查是否有成功抓取的源
        success_sources = [s for s in sources if s.get("status") == "success"]
        if not success_sources:
            print("❌ 错误：没有成功抓取的规则源，终止合并")
            sys.exit(1)

        # 步骤2: 加载头部模板
        print("步骤2: 加载头部模板")
        header_template = self.load_header_template()

        # 步骤3: 收集、处理和去重规则
        print("步骤3: 收集、处理和去重规则")
        rules, groups, source_stats = self.collect_and_process_rules(sources)
        self.initial_rule_count = sum(s["rule_count"] for s in source_stats)
        self.final_rule_count = sum(len(v) for v in groups.values())

        # 步骤4: 生成版本号
        print("步骤4: 生成版本号")
        version = self.generate_version()

        # 步骤5: 生成头部（单次 format_map 替代 11 次链式 replace）
        print("步骤5: 生成头部")
        source_list = self.generate_source_list(sources)
        now = datetime.now(UTC)  # 单次调用，消除重复
        header = header_template.format_map(
            _SafeDict(
                {
                    "VERSION": version,
                    "TIMEUPDATED": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "TIMEUPDATED_ISO": now.isoformat(),
                    "SOURCE_COUNT": str(len(success_sources)),
                    "SOURCE_LIST": source_list,
                    "COMBINED_RULES": str(self.final_rule_count),
                    "TOTAL_RULES": str(self.initial_rule_count),
                    "DUPLICATES": str(self.initial_rule_count - self.final_rule_count),
                    "HOMEPAGE": "https://github.com/Chaniug/FilterFusion",
                    "LICENSE": "MIT License",
                }
            )
        )
        # {CHECKSUM} 通过 _SafeDict.__missing__ 保持为字面占位符，后续单独替换

        # 构建最终内容
        content = header.rstrip("\n") + "\n" + "\n".join(rules)

        # 步骤6: 计算校验和（ABP 标准：MD5 + Base64）
        print("步骤6: 计算校验和（ABP 标准）")
        content_for_checksum = "\n".join(
            line for line in content.split("\n") if not line.startswith("! Checksum:")
        )
        md5_hash = hashlib.md5(content_for_checksum.encode("utf-8")).digest()
        checksum = base64.b64encode(md5_hash).decode("utf-8")
        content = content.replace("{CHECKSUM}", checksum)

        # 保存前检查规则数是否为 0
        if self.final_rule_count == 0:
            print("⚠️ 警告：合并后规则数为 0，不覆盖现有文件")
            return

        # 步骤7: 保存规则文件
        rule_filename = f"adblock-{version}.txt"
        rule_path = self.dist_dir / rule_filename
        print(f"保存规则文件到: {rule_path}")
        rule_path.write_text(content, encoding="utf-8")

        # 保存最新规则副本（直接复制内容）
        print("步骤7: 保存最新规则副本")
        main_path = self.dist_dir / "adblock-main.txt"
        if main_path.exists():
            main_path.unlink()
        shutil.copyfile(rule_path, main_path)

        # 计算处理时间
        processing_time = (datetime.now() - self.start_time).total_seconds()

        # 显示摘要
        print("\n" + "=" * 50)
        print("✅ 规则合并完成!")
        print("=" * 50)
        print(f"🔖 版本: {version}")
        print(f"📦 源规则数量: {self.initial_rule_count}")
        print(f"🪄 合并后规则数量: {self.final_rule_count}")
        print(f"♻️  重复规则: {self.initial_rule_count - self.final_rule_count}")
        print(f"⏱️  处理时间: {processing_time:.2f}秒")
        print(f"🔐 校验和: {checksum}")
        print(f"📄 合并规则文件: dist/{rule_filename}")
        print(f"📄 最新规则副本: dist/adblock-main.txt")

        # 步骤8: 保存摘要信息
        print("步骤8: 保存摘要信息")
        self.save_summary(version, checksum, source_stats, processing_time)

    def save_summary(
        self,
        version: str,
        checksum: str,
        source_stats: list[dict[str, Any]],
        processing_time: float,
    ) -> None:
        """保存摘要信息到 JSON 文件。"""
        summary = {
            "version": version,
            "date": datetime.now(UTC).isoformat(),
            "total_source_rules": self.initial_rule_count,
            "unique_rules": self.final_rule_count,
            "duplicates_removed": self.initial_rule_count - self.final_rule_count,
            "merge_time_seconds": round(processing_time, 2),
            "checksum": checksum,
            "sources": source_stats,
        }

        summary_path = self.dist_dir / "summary.json"
        print(f"保存摘要到: {summary_path}")
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        print("📊 摘要信息已保存至: dist/summary.json")


if __name__ == "__main__":
    merger = RuleMerger()
    try:
        merger.merge()
    except Exception as e:
        print(f"❌ 合并过程中发生致命错误: {e}")
        sys.exit(1)
