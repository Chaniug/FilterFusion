"""FilterFusion 规则合并模块 — 分类、去重、输出标准 ABP 格式。"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import tempfile
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
        "config_dir",
        "rules_dir",
        "initial_rule_count",
        "final_rule_count",
        "start_time",
        "_summary_list",
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

        self.dist_dir: Path = self.project_root / "dist"
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir: Path = self.project_root / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir: Path = self.project_root / "scripts"

        # 统计信息
        self.initial_rule_count: int = 0
        self.final_rule_count: int = 0
        self.start_time: datetime = datetime.now()
        # 累积多个 custom 规则的摘要，供 save_summary 统一写入 config/summary.json
        self._summary_list: list[dict[str, Any]] = []

    def load_metadata(self) -> dict[str, Any]:
        meta_path = Path(tempfile.gettempdir()) / "filterfusion" / "fetch_meta.json"

        if not meta_path.exists():
            print(f"❌ 找不到抓取元数据文件 {meta_path}")
            sys.exit(1)

        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            return data
        except json.JSONDecodeError as e:
            print(f"❌ 元数据文件格式不正确 {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 加载元数据出错: {e}")
            sys.exit(1)

    def load_header_template(self) -> str:
        header_path = self.project_root / "config" / "default.header"

        if not header_path.exists():
            print(f"❌ 找不到头部模板 {header_path}")
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

        print("收集和处理规则:", flush=True)
        for source in sources:
            if source.get("status") != "success":
                continue
            source_path = self.rules_dir / source["file"]
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
                print(f"⚠️ 处理 {source['name']} 出错: {e}")
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
        """生成版本号（YYYYMMDDHHMM，精确到分钟，可区分当天多次提交）。"""
        now = datetime.now(UTC)
        return f"{now.year}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute:02d}"

    def _do_merge(
        self,
        sources_to_merge: list[dict[str, Any]],
        sources_for_header: list[dict[str, Any]],
        output_filename: str,
        description: str,
        log_tag: str = "",
    ) -> tuple[int, int, float, list[dict[str, Any]], str]:
        """通用合并方法：加载头部 → 收集去重 → 校验和 → 保存到 dist/。

        返回 (initial_count, final_count, processing_time, source_stats, checksum)。
        """
        # 加载头部模板
        header_template = self.load_header_template()

        # 收集、处理和去重规则
        rules, groups, source_stats = self.collect_and_process_rules(sources_to_merge)
        initial_count = sum(s["rule_count"] for s in source_stats)
        final_count = sum(len(v) for v in groups.values())

        # 生成版本号
        version = self.generate_version()

        # 生成头部
        source_list = self.generate_source_list(sources_for_header)
        now = datetime.now(UTC)
        header = header_template.format_map(
            _SafeDict(
                {
                    "VERSION": version,
                    "TIMEUPDATED": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "TIMEUPDATED_ISO": now.isoformat(),
                    "DESCRIPTION": description,
                    "SOURCE_COUNT": str(len(sources_for_header)),
                    "SOURCE_LIST": source_list,
                    "COMBINED_RULES": str(final_count),
                    "TOTAL_RULES": str(initial_count),
                    "DUPLICATES": str(initial_count - final_count),
                    "HOMEPAGE": "https://github.com/Chaniug/FilterFusion",
                    "LICENSE": "MIT License",
                }
            )
        )

        # 构建最终内容
        content = header.rstrip("\n") + "\n" + "\n".join(rules)

        # 计算校验和（ABP 标准：MD5 + Base64）
        content_for_checksum = "\n".join(
            line for line in content.split("\n") if not line.startswith("! Checksum:")
        )
        md5_hash = hashlib.md5(content_for_checksum.encode("utf-8")).digest()
        checksum = base64.b64encode(md5_hash).decode("utf-8")
        content = content.replace("{CHECKSUM}", checksum)

        # 保存前检查规则数是否为 0
        if final_count == 0:
            print("⚠️ 合并后规则数为 0，不覆盖现有文件")
            return initial_count, final_count, 0.0, source_stats, checksum

        # 保存规则文件
        rule_path = self.dist_dir / output_filename
        rule_path.write_text(content, encoding="utf-8")

        # 计算处理时间
        processing_time = (datetime.now() - self.start_time).total_seconds()

        tag = f" [{log_tag}]" if log_tag else ""
        print(f"✅ AdBlock{tag} 合并完成: {initial_count} → {final_count} 条 (去重 {initial_count - final_count}, {processing_time:.2f}s) → dist/{output_filename}")

        return initial_count, final_count, processing_time, source_stats, checksum

    def merge_custom(
        self, output_filename: str, source_ids: list[str], description: str = ""
    ) -> None:
        """合并自定义组合规则：按 ID 查找源 → 按 file 去重 → 合并去重 → 输出到 dist/。

        Args:
            output_filename: 输出文件名（如 adblock-mo.txt）
            source_ids: 要引用的源 ID 列表（如 ["m1", "m2", "b1"]）
            description: 可选的规则描述文本，不填则自动生成
        """
        # 加载元数据
        metadata = self.load_metadata()
        sources: list[dict[str, Any]] = metadata["sources"]

        # 按 ID 查找源记录
        id_to_sources: dict[str, list[dict[str, Any]]] = {}
        for s in sources:
            sid = s.get("id")
            if sid:
                id_to_sources.setdefault(sid, []).append(s)

        # 收集要合并的源（按 ID 引用，按 file 去重避免 B 源重复处理）
        sources_to_merge: list[dict[str, Any]] = []
        seen_files: set[str] = set()
        for sid in source_ids:
            matched = id_to_sources.get(sid)
            if not matched:
                print(f"⚠️ 组合规则 '{output_filename}' 引用的 ID '{sid}' 不存在，跳过")
                continue
            for s in matched:
                file_name = s.get("file", "")
                if file_name and file_name in seen_files:
                    continue  # 同一文件已加入，跳过
                if file_name:
                    seen_files.add(file_name)
                if s.get("status") == "success":
                    sources_to_merge.append(s)

        if not sources_to_merge:
            print(f"⚠️ 组合规则 '{output_filename}' 没有可用的源，跳过")
            return

        print(f"🔖 组合规则 [{output_filename}]: {len(source_ids)} 个 ID → {len(sources_to_merge)} 个源", flush=True)

        # 生成描述：优先使用配置中的 description，否则自动生成
        if description:
            desc = description
        else:
            name_without_ext = output_filename.rsplit(".", 1)[0] if "." in output_filename else output_filename
            desc = f"FilterFusion - Custom combined rules ({name_without_ext})"

        # 重置 start_time 用于此组合规则单独计时
        self.start_time = datetime.now()

        # 调用通用合并方法（头部 SOURCE_LIST 用合并的源列表）
        initial_count, final_count, processing_time, source_stats, checksum = self._do_merge(
            sources_to_merge=sources_to_merge,
            sources_for_header=sources_to_merge,
            output_filename=output_filename,
            description=desc,
            log_tag=output_filename,
        )

        # 累积摘要（暂存内存，由 flush_summary 统一落盘到 config/summary.json）
        version = self.generate_version()
        self._summary_list.append({
            "output": output_filename,
            "version": version,
            "date": datetime.now(UTC).isoformat(),
            "total_source_rules": initial_count,
            "unique_rules": final_count,
            "duplicates_removed": initial_count - final_count,
            "merge_time_seconds": round(processing_time, 2),
            "checksum": checksum,
            "sources": source_stats,
        })

    def flush_summary(self) -> None:
        """将累积的所有 custom 规则摘要写入 config/summary.json。

        每次 merge_custom 调用会把摘要追加到 _summary_list，
        最后由 merge_all 统一调用本方法落盘，避免多次覆盖。
        """
        if not self._summary_list:
            return
        summary_path = self.config_dir / "summary.json"
        summary = {
            "generated_at": datetime.now(UTC).isoformat(),
            "rule_sets": self._summary_list,
        }
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"📝 AdBlock 摘要已写入 config/summary.json（{len(self._summary_list)} 个规则集）")


if __name__ == "__main__":
    print("此模块不直接运行，请使用统一入口：python -m scripts.merge_all")
    sys.exit(1)
