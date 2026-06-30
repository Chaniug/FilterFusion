"""统一入口 — 单进程完成抓取 + 合并，消除两次 Python 进程启动开销。

保留 scripts.fetch_all 和 scripts.merge_all 作为独立入口向后兼容，
CI 默认使用本入口以省去一次 uv run + Python 解释器初始化（约 1-2s）。
"""

from __future__ import annotations

import asyncio
import sys
import time

from scripts.fetch_all import main as fetch_main
from scripts.merge_all import main as merge_main


def main() -> None:
    print("🚀 FilterFusion - 单进程抓取 + 合并", flush=True)
    start = time.perf_counter()

    # 阶段 1：异步抓取（fetch_all 内部用 gather 并发 AdBlock + DNS）
    asyncio.run(fetch_main())

    # 阶段 2：同步合并（merge_all 内部依次执行 DNS + AdBlock custom_rules）
    merge_main()

    elapsed = time.perf_counter() - start
    print(f"✅ 单进程抓取 + 合并完成，总耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 执行过程发生错误: {e}")
        sys.exit(1)
