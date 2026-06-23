"""统一的合并入口 — 在单个进程中顺序执行 AdBlock (Mobile/PC) 和 DNS 规则合并。

消除 2 次 uv run + Python 进程启动开销。
"""

from __future__ import annotations

import sys
import time

from scripts.merge_dns_rules import DnsRuleMerger
from scripts.merge_rules import RuleMerger


def main() -> None:
    print("🔧 FilterFusion - 统一规则合并", flush=True)
    start = time.perf_counter()

    # 顺序执行 3 个合并任务（mobile → pc → DNS）
    RuleMerger(category="mobile").merge()
    RuleMerger(category="pc").merge()
    DnsRuleMerger().merge()

    elapsed = time.perf_counter() - start
    print(f"✅ 全部合并完成，总耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 统一合并过程发生错误: {e}")
        sys.exit(1)
