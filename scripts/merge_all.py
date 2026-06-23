"""统一的合并入口 — 在单个进程中执行 DNS 规则合并和 AdBlock custom_rules 组合规则。

消除多次 uv run + Python 进程启动开销。
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.merge_dns_rules import DnsRuleMerger
from scripts.merge_rules import RuleMerger


def main() -> None:
    print("🔧 FilterFusion - 统一规则合并", flush=True)
    start = time.perf_counter()

    # DNS 规则合并（独立管道，不在 custom_rules 范畴）
    DnsRuleMerger().merge()

    # AdBlock 规则合并（全部由 config/sources.yaml 的 custom_rules 驱动）
    meta_path = Path(tempfile.gettempdir()) / "filterfusion" / "fetch_meta.json"
    if meta_path.exists():
        try:
            meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            meta = {}
        custom_rules = meta.get("custom_rules") or []
        if custom_rules:
            print(f"\n📦 处理 {len(custom_rules)} 个组合规则", flush=True)
            merger = RuleMerger()
            for rule in custom_rules:
                output = rule.get("output", "")
                source_ids = rule.get("sources") or []
                description = rule.get("description", "")
                if output and source_ids:
                    merger.merge_custom(output, source_ids, description)
        else:
            print("\n⚠️ 没有定义任何 custom_rules，跳过 AdBlock 规则合并")

    elapsed = time.perf_counter() - start
    print(f"✅ 全部合并完成，总耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 统一合并过程发生错误: {e}")
        sys.exit(1)
