"""FilterFusion 规则抓取模块 — 基于 httpx 异步客户端 + HTTP/2 多路复用。"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import tempfile
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx

type SourceInfo = dict[str, Any]
type SourceMeta = dict[str, Any]


class FetchStatus(StrEnum):
    """抓取状态枚举（StrEnum 兼容 JSON 序列化）。"""

    SUCCESS = "success"
    FAILED = "failed"
    DISABLED = "disabled"


class RuleFetcher:
    """异步抓取多源广告过滤规则。

    使用 httpx.AsyncClient 单例，HTTP/2 多路复用，复用 TLS 连接。
    """

    __slots__ = ("project_root", "rules_dir", "meta_file")

    def __init__(self) -> None:
        self.project_root: Path = Path(__file__).resolve().parent.parent
        print(f"项目根目录: {self.project_root}")

        self.rules_dir: Path = self.project_root / "scripts"
        self.meta_file: Path = Path(tempfile.gettempdir()) / "filterfusion" / "fetch_meta.json"
        self.meta_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"规则目录: {self.rules_dir}")
        print(f"元数据文件: {self.meta_file}")

    def load_sources(self) -> list[SourceInfo]:
        """从 config/sources.txt 加载规则源配置。

        格式: [M|P]>名称 > 订阅地址；行首加 # 表示禁用。
        M: 移动端 (Mobile), P: 电脑端 (PC/Desktop)，无前缀默认为 M。
        """
        config_path = self.project_root / "config" / "sources.txt"
        print(f"配置文件路径: {config_path}")

        if not config_path.exists():
            print(f"❌ 错误：找不到配置文件 {config_path}")
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

                # 解析 [M|P]>名称 > URL
                if ">" not in raw:
                    print(f"⚠️ 第 {line_num} 行格式错误（缺少 >）: {raw}")
                    continue

                parts = [p.strip() for p in raw.split(">", 2)]
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

                category = "pc" if prefix.upper() == "P" else "mobile"

                sources.append({
                    "name": name,
                    "url": url,
                    "category": category,
                    "enabled": not disabled,
                })

            print(f"加载了 {len(sources)} 个规则源")
            return sources
        except Exception as e:
            print(f"❌ 加载配置文件时出错: {e}")
            sys.exit(1)

    async def fetch_single_rule(self, source: SourceInfo, client: httpx.AsyncClient) -> SourceMeta:
        """异步抓取单个规则源，带 3 次重试与递增超时。"""
        retry_count = 3
        for attempt in range(1, retry_count + 1):
            try:
                print(f"⬇️  抓取规则: {source['name']} (尝试 {attempt}/{retry_count})...", end=" ", flush=True)
                # 递增超时：35s → 50s → 65s，适配大型规则文件
                timeout = 20 + attempt * 15
                response = await client.get(source["url"], timeout=timeout)
                response.raise_for_status()

                # 生成安全的文件名
                safe_name = source["name"].replace(" ", "_").lower().replace(".", "")
                filename = f"{safe_name}.txt"
                filepath = self.rules_dir / filename

                # 流式写入：直接写 bytes，避免编码开销
                filepath.write_bytes(response.content)

                file_hash = hashlib.sha256(response.content).hexdigest()
                timestamp = datetime.now(UTC).isoformat()

                print("✓")
                return {
                    "name": source["name"],
                    "file": filename,
                    "url": source["url"],
                    "timestamp": timestamp,
                    "hash": file_hash,
                    "status": FetchStatus.SUCCESS,
                }
            except httpx.TimeoutException:
                if attempt < retry_count:
                    print("超时，重试...", end=" ")
                    continue
                print("✗ (超时)")
                return {
                    "name": source["name"],
                    "url": source["url"],
                    "status": FetchStatus.FAILED,
                    "error": "请求超时",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            except httpx.HTTPError as e:
                if attempt < retry_count:
                    print(f"错误 ({e}), 重试...", end=" ")
                    continue
                print(f"✗ ({e})")
                return {
                    "name": source["name"],
                    "url": source["url"],
                    "status": FetchStatus.FAILED,
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat(),
                }

        # 理论不可达：循环内已覆盖所有分支返回
        return {
            "name": source["name"],
            "url": source["url"],
            "status": FetchStatus.FAILED,
            "error": "重试次数耗尽",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def fetch_all_rules(self) -> dict[str, Any]:
        """并发抓取所有已启用的规则源。"""
        sources = self.load_sources()
        results: list[SourceMeta] = []

        print("\n" + "=" * 50)
        print("🔍 开始抓取广告过滤规则...")
        print(f"📡 共检测到 {len(sources)} 个规则源")
        print("=" * 50)

        # 分离启用/禁用的源
        enabled_sources = [s for s in sources if s.get("enabled", True)]
        disabled_sources = [s for s in sources if not s.get("enabled", True)]

        # 记录禁用的源
        for source in disabled_sources:
            print(f"⏭️  跳过禁用规则: {source['name']}")
            results.append({
                "name": source["name"],
                "url": source["url"],
                "status": FetchStatus.DISABLED,
            })

        # 异步并发下载启用的源
        print(f"\n🚀 开始并发下载 {len(enabled_sources)} 个启用的规则源...")
        if enabled_sources:
            async with httpx.AsyncClient(
                http2=True,
                headers={"User-Agent": "FilterFusion/1.0 (+https://github.com/Chaniug/FilterFusion)"},
                follow_redirects=True,
            ) as client:
                # asyncio.gather 原生并发，无线程开销
                fetched = await asyncio.gather(
                    *(self.fetch_single_rule(s, client) for s in enabled_sources)
                )
                results.extend(fetched)

        # 保存元数据
        meta = {
            "fetch_date": datetime.now(UTC).isoformat(),
            "sources": results,
        }
        self.meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        # 统计
        success = sum(1 for s in results if s["status"] == FetchStatus.SUCCESS)
        failed = sum(1 for s in results if s["status"] == FetchStatus.FAILED)

        print("\n" + "=" * 50)
        print(f"✅ 抓取完成: 成功 {success} 个, 失败 {failed} 个")
        print("=" * 50)

        if failed > 0:
            print("\n失败的来源:")
            for source in results:
                if source["status"] == FetchStatus.FAILED:
                    print(f"  - {source['name']}: {source.get('error', '未知错误')}")

        print(f"抓取元数据已保存至: {self.meta_file}")
        return meta


async def main() -> None:
    print("=" * 50)
    print("🚀 FilterFusion - 广告规则抓取工具")
    print("=" * 50)

    fetcher = RuleFetcher()
    try:
        await fetcher.fetch_all_rules()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
