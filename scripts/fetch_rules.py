"""FilterFusion AdBlock 规则抓取模块 — 基于 httpx 异步客户端 + HTTP/2 多路复用。"""

from __future__ import annotations

import asyncio
import sys

from scripts.base_fetcher import BaseFetcher, SourceInfo


class RuleFetcher(BaseFetcher):
    """异步抓取多源广告过滤规则。

    使用 httpx.AsyncClient 单例，HTTP/2 多路复用，复用 TLS 连接。
    """

    def __init__(self) -> None:
        super().__init__(meta_filename="fetch_meta.json", filename_prefix="", log_tag="广告")

    def load_sources(self) -> list[SourceInfo]:
        """从 config/sources.txt 加载规则源配置。

        格式: [M|P|B]|名称|订阅地址
        M: 移动端 (Mobile), P: 电脑端 (PC), B: 两端共用 (Both)
        无前缀默认为 M。B 会展开为 mobile 和 pc 两条记录（URL 相同，去重下载）。
        """
        config_path = self.project_root / "config" / "sources.txt"

        if not config_path.exists():
            print(f"❌ 找不到配置文件 {config_path}")
            sys.exit(1)

        sources: list[SourceInfo] = []
        try:
            for line_num, raw_line in enumerate(config_path.read_text(encoding="utf-8").splitlines(), 1):
                raw = raw_line.strip()
                if not raw:
                    continue

                # 判断是否被禁用（行首 # 且包含 |）
                disabled = False
                if raw.startswith("#"):
                    content = raw[1:].strip()
                    if "|" not in content:
                        continue  # 纯注释行，跳过
                    disabled = True
                    raw = content

                # 解析 [M|P|B]|名称|URL
                if "|" not in raw:
                    print(f"⚠️ 第 {line_num} 行格式错误（缺少 |）: {raw}")
                    continue

                parts = [p.strip() for p in raw.split("|", 2)]
                if len(parts) == 3:
                    prefix, name, url = parts
                elif len(parts) == 2:
                    name, url = parts
                    prefix = "M"
                else:
                    continue

                if not name or not url:
                    print(f"⚠️ 第 {line_num} 行名称或地址为空: {raw}")
                    continue

                # 校验 URL 格式（必须以 http 开头）
                if not url.startswith("http"):
                    continue  # 非有效 URL，视为纯注释行

                prefix_upper = prefix.upper()

                # B> 展开为 mobile + pc 两条记录（URL 相同，fetch 阶段按 URL 去重）
                if prefix_upper == "B":
                    sources.append({
                        "name": name,
                        "url": url,
                        "category": "mobile",
                        "enabled": not disabled,
                    })
                    sources.append({
                        "name": name,
                        "url": url,
                        "category": "pc",
                        "enabled": not disabled,
                    })
                else:
                    category = "pc" if prefix_upper == "P" else "mobile"
                    sources.append({
                        "name": name,
                        "url": url,
                        "category": category,
                        "enabled": not disabled,
                    })

            print(f"加载了 {len(sources)} 个规则源")
            return sources
        except Exception as e:
            print(f"❌ 加载配置出错: {e}")
            sys.exit(1)


async def main() -> None:
    fetcher = RuleFetcher()
    try:
        await fetcher.fetch_all_rules()
    except Exception as e:
        print(f"\n❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
