"""统一的抓取入口 — 在单个进程中同时执行 AdBlock 和 DNS 规则抓取。

消除两次 uv run + Python 进程启动开销，共享事件循环。
"""

from __future__ import annotations

import asyncio
import sys
import time

from scripts.fetch_rules import main as fetch_adblock
from scripts.fetch_dns_rules import main as fetch_dns


async def main() -> None:
    print("=" * 50)
    print("🚀 FilterFusion - 统一规则抓取入口")
    print("=" * 50)
    start = time.perf_counter()

    # 在同一个事件循环中并发执行两个抓取任务
    await asyncio.gather(fetch_adblock(), fetch_dns())

    elapsed = time.perf_counter() - start
    print(f"\n✅ 全部抓取完成，总耗时: {elapsed:.2f}秒")
    print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 统一抓取过程发生错误: {e}")
        sys.exit(1)
