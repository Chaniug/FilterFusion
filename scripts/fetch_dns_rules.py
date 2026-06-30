"""FilterFusion DNS 规则抓取模块 — 基于 httpx 异步客户端 + HTTP/2 多路复用。"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import yaml

from scripts.base_fetcher import BaseFetcher, SourceInfo


class DnsRuleFetcher(BaseFetcher):
    """异步抓取多源 DNS 过滤规则。

    使用 httpx.AsyncClient 单例，HTTP/2 多路复用，复用 TLS 连接。
    """

    def __init__(self) -> None:
        super().__init__(meta_filename="dns_fetch_meta.json", filename_prefix="dns_", log_tag="DNS")

    def load_sources(self) -> list[SourceInfo]:
        """从 config/dns_sources.yaml 加载 DNS 规则源配置。

        YAML 格式:
          sources:
            - name: AdGuard DNS
              url: https://...
        """
        config_path = self.project_root / "config" / "dns_sources.yaml"

        if not config_path.exists():
            print(f"❌ 找不到 DNS 配置文件 {config_path}")
            sys.exit(1)

        sources: list[SourceInfo] = []
        try:
            data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            print(f"❌ YAML 解析失败: {e}")
            sys.exit(1)

        raw_sources = data.get("sources") or []
        for idx, item in enumerate(raw_sources, 1):
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()

            if not name or not url:
                print(f"⚠️ 第 {idx} 个 DNS 源缺少 name 或 url，跳过")
                continue

            if not url.startswith("http"):
                print(f"⚠️ 第 {idx} 个 DNS 源 url 无效: {url}")
                continue

            sources.append({
                "name": name,
                "url": url,
                "enabled": True,
            })

        print(f"加载了 {len(sources)} 个 DNS 规则源", flush=True)
        return sources


async def main() -> None:
    fetcher = DnsRuleFetcher()
    try:
        await fetcher.fetch_all_rules()
    except Exception as e:
        print(f"\n❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
