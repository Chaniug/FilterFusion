"""FilterFusion 规则抓取基类 — 基于 httpx 异步客户端 + HTTP/2 多路复用。

AdBlock 和 DNS 两条管道的抓取逻辑高度一致，共享部分抽取至此基类，
子类只需实现 load_sources() 定义各自的配置解析格式。
"""

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


class BaseFetcher:
    """异步抓取多源规则的基类。

    使用 httpx.AsyncClient 单例，HTTP/2 多路复用，复用 TLS 连接。
    子类只需实现 load_sources() 定义配置解析逻辑。
    """

    __slots__ = ("project_root", "rules_dir", "meta_file", "filename_prefix", "log_tag")

    def __init__(
        self,
        *,
        meta_filename: str,
        filename_prefix: str = "",
        log_tag: str = "",
    ) -> None:
        self.project_root: Path = Path(__file__).resolve().parent.parent
        print(f"项目根目录: {self.project_root}")

        self.rules_dir: Path = self.project_root / "scripts"
        self.meta_file: Path = Path(tempfile.gettempdir()) / "filterfusion" / meta_filename
        self.meta_file.parent.mkdir(parents=True, exist_ok=True)
        self.filename_prefix: str = filename_prefix
        self.log_tag: str = log_tag or meta_filename

        print(f"规则目录: {self.rules_dir}")
        print(f"元数据文件: {self.meta_file}")

    def load_sources(self) -> list[SourceInfo]:
        """从配置文件加载规则源配置。子类必须实现。"""
        raise NotImplementedError

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

                # 生成安全的文件名（可加前缀区分不同管道）
                safe_name = self.filename_prefix + source["name"].replace(" ", "_").lower().replace(".", "")
                filename = f"{safe_name}.txt"
                filepath = self.rules_dir / filename

                # 流式写入：直接写 bytes，避免编码开销
                filepath.write_bytes(response.content)

                file_hash = hashlib.sha256(response.content).hexdigest()
                timestamp = datetime.now(UTC).isoformat()

                print("✓")
                return self._build_success(source, filename, file_hash, timestamp)
            except httpx.TimeoutException:
                if attempt < retry_count:
                    print("超时，重试...", end=" ")
                    continue
                print("✗ (超时)")
                return self._build_failure(source, "请求超时")
            except httpx.HTTPError as e:
                if attempt < retry_count:
                    print(f"错误 ({e}), 重试...", end=" ")
                    continue
                print(f"✗ ({e})")
                return self._build_failure(source, str(e))

        # 理论不可达：循环内已覆盖所有分支返回
        return self._build_failure(source, "重试次数耗尽")

    def _build_success(self, source: SourceInfo, filename: str, file_hash: str, timestamp: str) -> SourceMeta:
        """构建成功返回的元数据。"""
        result: SourceMeta = {
            "name": source["name"],
            "file": filename,
            "url": source["url"],
            "timestamp": timestamp,
            "hash": file_hash,
            "status": FetchStatus.SUCCESS,
        }
        if "category" in source:
            result["category"] = source["category"]
        return result

    def _build_failure(self, source: SourceInfo, error: str) -> SourceMeta:
        """构建失败返回的元数据。"""
        result: SourceMeta = {
            "name": source["name"],
            "url": source["url"],
            "status": FetchStatus.FAILED,
            "error": error,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if "category" in source:
            result["category"] = source["category"]
        return result

    def _build_disabled(self, source: SourceInfo) -> SourceMeta:
        """构建禁用返回的元数据。"""
        result: SourceMeta = {
            "name": source["name"],
            "url": source["url"],
            "status": FetchStatus.DISABLED,
        }
        if "category" in source:
            result["category"] = source["category"]
        return result

    async def fetch_all_rules(self) -> dict[str, Any]:
        """并发抓取所有已启用的规则源。"""
        sources = self.load_sources()
        results: list[SourceMeta] = []

        print("\n" + "=" * 50)
        print(f"🔍 开始抓取{self.log_tag}规则...")
        print(f"📡 共检测到 {len(sources)} 个规则源")
        print("=" * 50)

        # 分离启用/禁用的源
        enabled_sources = [s for s in sources if s.get("enabled", True)]
        disabled_sources = [s for s in sources if not s.get("enabled", True)]

        # 记录禁用的源
        for source in disabled_sources:
            print(f"⏭️  跳过禁用规则: {source['name']}")
            results.append(self._build_disabled(source))

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
        print(f"✅ {self.log_tag}规则抓取完成: 成功 {success} 个, 失败 {failed} 个")
        print("=" * 50)

        if failed > 0:
            print("\n失败的来源:")
            for source in results:
                if source["status"] == FetchStatus.FAILED:
                    print(f"  - {source['name']}: {source.get('error', '未知错误')}")

        print(f"抓取元数据已保存至: {self.meta_file}")
        return meta
