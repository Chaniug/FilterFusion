"""FilterFusion DNS 规则合并模块 — 去重、输出标准 DNS 过滤格式。"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class DnsRuleMerger:
    """DNS 规则合并器：读取抓取产物 → 去重 → 输出标准格式。

    DNS 规则合并比 AdBlock 规则合并简单，因为：
    - DNS 规则是 AdBlock 规则的子集，不支持元素隐藏、HTML 过滤等浏览器专属语法
    - 不需要复杂的规则分类逻辑，主要是域名去重
    - 不需要 ABP 校验和计算
    """

    __slots__ = (
        "project_root",
        "dist_dir",
        "rules_dir",
        "initial_rule_count",
        "final_rule_count",
        "start_time",
    )

    def __init__(self) -> None:
        self.project_root: Path = Path(__file__).resolve().parent.parent
        print(f"项目根目录: {self.project_root}")

        self.dist_dir: Path = self.project_root / "dist"
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir: Path = self.project_root / "scripts"

        print(f"分发目录: {self.dist_dir}")
        print(f"规则目录: {self.rules_dir}")

        # 统计信息
        self.initial_rule_count: int = 0
        self.final_rule_count: int = 0
        self.start_time: datetime = datetime.now()

    def load_metadata(self) -> dict[str, Any]:
        """加载 DNS 规则抓取元数据。"""
        meta_path = Path(tempfile.gettempdir()) / "filterfusion" / "dns_fetch_meta.json"
        print(f"尝试加载 DNS 元数据: {meta_path}")

        if not meta_path.exists():
            print(f"❌ 错误：找不到 DNS 抓取元数据文件 {meta_path}")
            sys.exit(1)

        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            print("成功加载 DNS 元数据文件")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ 错误：DNS 元数据文件格式不正确 {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 加载 DNS 元数据时出错: {e}")
            sys.exit(1)

    def load_header_template(self) -> str:
        """加载 DNS 规则头部模板。"""
        header_path = self.project_root / "config" / "dns.header"
        print(f"尝试加载 DNS 头部模板: {header_path}")

        if not header_path.exists():
            print(f"❌ 错误：找不到 DNS 头部模板 {header_path}")
            sys.exit(1)

        try:
            return header_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"❌ 读取 DNS 头部模板失败: {e}")
            sys.exit(1)

    def generate_source_list(self, sources: list[dict[str, Any]]) -> str:
        """生成格式化的 DNS 源列表信息。"""
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

    def collect_and_dedup_rules(
        self, sources: list[dict[str, Any]]
    ) -> tuple[list[str], list[dict[str, Any]], int]:
        """收集并去重 DNS 规则：主要做域名去重，不需要复杂的规则分类。"""
        # DNS 规则分类：例外规则（@@ 开头）和普通规则
        exception_rules: set[str] = set()
        normal_rules: set[str] = set()
        seen_rules: set[str] = set()
        source_stats: list[dict[str, Any]] = []

        print("收集和去重 DNS 规则:")
        for source in sources:
            if source.get("status") != "success":
                continue
            source_path = self.rules_dir / source["file"]
            print(f"处理 DNS 源文件: {source_path}")
            if not source_path.exists():
                continue

            source_rule_count = 0
            source_seen: set[str] = set()  # 源内去重（独立于全局）
            try:
                with open(source_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        rule = line.strip()
                        if not rule:
                            continue

                        # 跳过注释行（但以 ! 开头的注释保留在头部，这里跳过）
                        if rule.startswith("!"):
                            continue

                        # 跳过 AdBlock Plus 格式声明（DNS 规则不需要）
                        if rule.startswith("[Adblock"):
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

                        # 分类：例外规则（@@ 开头）和普通规则
                        if rule.startswith("@@"):
                            exception_rules.add(rule)
                        else:
                            normal_rules.add(rule)
            except Exception as e:
                print(f"⚠️ 警告：处理 {source['name']} DNS 规则时出错: {e}")
            print(f"DNS 源 {source['name']} 有效规则数: {source_rule_count}")
            source_stats.append({"name": source["name"], "rule_count": source_rule_count})

        # 按分组分类拼接输出
        merged_lines: list[str] = []
        if exception_rules:
            merged_lines.append("! === 例外规则 Exception Rules ===")
            merged_lines.extend(sorted(exception_rules))
            merged_lines.append("")
        if normal_rules:
            merged_lines.append("! === DNS 过滤规则 DNS Blocking Rules ===")
            merged_lines.extend(sorted(normal_rules))
            merged_lines.append("")

        total = len(exception_rules) + len(normal_rules)
        print(f"收集了 {total} 条唯一 DNS 规则")
        return merged_lines, source_stats, total

    @staticmethod
    def generate_version() -> str:
        """生成简单的语义化版本号（YYYYMMDD）。"""
        today = datetime.now(UTC)
        return f"{today.year}{today.month:02d}{today.day:02d}"

    def merge(self) -> None:
        print("=" * 50)
        print("🔧 FilterFusion - DNS 规则合并工具")
        print("=" * 50)

        # 步骤1: 加载元数据
        print("步骤1: 加载 DNS 元数据")
        metadata = self.load_metadata()
        sources = metadata["sources"]

        # 检查是否有成功抓取的源
        success_sources = [s for s in sources if s.get("status") == "success"]
        if not success_sources:
            print("❌ 错误：没有成功抓取的 DNS 规则源，终止合并")
            sys.exit(1)

        # 步骤2: 加载头部模板
        print("步骤2: 加载 DNS 头部模板")
        header_template = self.load_header_template()

        # 步骤3: 收集、处理和去重规则
        print("步骤3: 收集、处理和去重 DNS 规则")
        rules, source_stats, self.final_rule_count = self.collect_and_dedup_rules(sources)
        self.initial_rule_count = sum(s["rule_count"] for s in source_stats)

        # 步骤4: 生成版本号
        print("步骤4: 生成版本号")
        version = self.generate_version()

        # 步骤5: 生成头部（单次 format_map 替代 8 次链式 replace）
        print("步骤5: 生成头部")
        source_list = self.generate_source_list(sources)
        now = datetime.now(UTC)  # 单次调用，消除重复
        header = header_template.format_map(
            {
                "VERSION": version,
                "TIMEUPDATED": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "SOURCE_COUNT": str(len(success_sources)),
                "SOURCE_LIST": source_list,
                "TOTAL_RULES": str(self.final_rule_count),
                "DUPLICATES": str(self.initial_rule_count - self.final_rule_count),
                "HOMEPAGE": "https://github.com/Chaniug/FilterFusion",
                "LICENSE": "MIT License",
            }
        )

        # 构建最终内容
        content = header.rstrip("\n") + "\n" + "\n".join(rules)

        # 保存前检查规则数是否为 0
        if self.final_rule_count == 0:
            print("⚠️ 警告：合并后 DNS 规则数为 0，不覆盖现有文件")
            return

        # 步骤6: 保存规则文件（直接写入规范文件名，不生成日期快照）
        rule_path = self.dist_dir / "dns-blocklist.txt"
        print(f"保存 DNS 规则文件到: {rule_path}")
        rule_path.write_text(content, encoding="utf-8")

        # 计算处理时间
        processing_time = (datetime.now() - self.start_time).total_seconds()

        # 显示摘要
        print("\n" + "=" * 50)
        print("✅ DNS 规则合并完成!")
        print("=" * 50)
        print(f"🔖 版本: {version}")
        print(f"📦 源规则数量: {self.initial_rule_count}")
        print(f"🪄 合并后规则数量: {self.final_rule_count}")
        print(f"♻️  重复规则: {self.initial_rule_count - self.final_rule_count}")
        print(f"⏱️  处理时间: {processing_time:.2f}秒")
        print(f"📄 合并规则文件: dist/dns-blocklist.txt")

        # 步骤7: 保存摘要信息
        print("步骤7: 保存 DNS 摘要信息")
        self.save_summary(version, source_stats, processing_time)

    def save_summary(
        self,
        version: str,
        source_stats: list[dict[str, Any]],
        processing_time: float,
    ) -> None:
        """打印 DNS 合并摘要信息到控制台。"""
        summary = {
            "version": version,
            "date": datetime.now(UTC).isoformat(),
            "total_source_rules": self.initial_rule_count,
            "unique_rules": self.final_rule_count,
            "duplicates_removed": self.initial_rule_count - self.final_rule_count,
            "merge_time_seconds": round(processing_time, 2),
            "sources": source_stats,
        }

        print("📊 DNS 合并摘要:")
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    merger = DnsRuleMerger()
    try:
        merger.merge()
    except Exception as e:
        print(f"❌ DNS 规则合并过程中发生致命错误: {e}")
        sys.exit(1)
