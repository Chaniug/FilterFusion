"""FilterFusion DNS 规则抓取模块 — 基于 httpx 异步客户端 + HTTP/2 多路复用。"""

from __future__ import annotations

import asyncio
import sys

from scripts.base_fetcher import BaseFetcher, SourceInfo


class DnsRuleFetcher(BaseFetcher):
    """异步抓取多源 DNS 过滤规则。

    使用 httpx.AsyncClient 单例，HTTP/2 多路复用，复用 TLS 连接。
    """

    def __init__(self) -> None:
        super().__init__(meta_filename="dns_fetch_meta.json", filename_prefix="dns_", log_tag="DNS")

    def load_sources(self) -> list[SourceInfo]:
        """从 config/dns_sources.txt 加载 DNS 规则源配置。

        格式: 名称 > 订阅地址；行首加 # 表示禁用。
        """
        config_path = self.project_root / "config" / "dns_sources.txt"
        print(f"DNS 配置文件路径: {config_path}")

        if not config_path.exists():
            print(f"❌ 错误：找不到 DNS 配置文件 {config_path}")
            sys.exit(1)

        sources: list[SourceInfo] = []
        try:
            for line_num, raw_line in enumerate(config_path.read_text(encoding="utf-8").splitlines(), 1):
                raw = raw_line.strip()
                if not raw:
                    continue

                # 判断是否被禁用（行首 # 且包含 >）
                disabled = False
                if raw.startswith("#"):
                    content = raw[1:].strip()
                    if ">" not in content:
                        continue  # 纯注释行，跳过
                    disabled = True
                    raw = content

                # 解析 名称 > URL
                if ">" not in raw:
                    print(f"⚠️ 第 {line_num} 行格式错误（缺少 >）: {raw}")
                    continue

                name, url = (part.strip() for part in raw.split(">", 1))
                if not name or not url:
                    print(f"⚠️ 第 {line_num} 行名称或地址为空: {raw}")
                    continue

                # 校验 URL 格式（必须以 http 开头）
                if not url.startswith("http"):
                    continue  # 非有效 URL，视为纯注释行

                sources.append({
                    "name": name,
                    "url": url,
                    "enabled": not disabled,
                })

            print(f"加载了 {len(sources)} 个 DNS 规则源")
            return sources
        except Exception as e:
            print(f"❌ 加载 DNS 配置文件时出错: {e}")
            sys.exit(1)


async def main() -> None:
    print("=" * 50)
    print("🚀 FilterFusion - DNS 规则抓取工具")
    print("=" * 50)

    fetcher = DnsRuleFetcher()
    try:
        await fetcher.fetch_all_rules()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
