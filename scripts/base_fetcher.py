"""FilterFusion 规则抓取基类 — 基于 httpx 异步客户端 + HTTP/2 多路复用。

AdBlock 和 DNS 两条管道的抓取逻辑高度一致，共享部分抽取至此基类，
子类只需实现 load_sources() 定义各自的配置解析格式。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import sys
import tempfile
from datetime import UTC, datetime
from enum import StrEnum
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx

# 并发抓取上限：对 raw.githubusercontent.com 友好的保守值，避免触发 429 限流
_MAX_CONCURRENT_FETCH = 8

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

    支持按 URL 去重：同 URL 的多个源（如 B> 展开为 mobile+pc）只下载一次，
    多条 source 记录共享同一个本地文件。
    """

    __slots__ = ("project_root", "rules_dir", "meta_file", "filename_prefix", "log_tag", "custom_rules")

    def __init__(
        self,
        *,
        meta_filename: str,
        filename_prefix: str = "",
        log_tag: str = "",
    ) -> None:
        self.project_root: Path = Path(__file__).resolve().parent.parent

        self.rules_dir: Path = self.project_root / "scripts"
        self.meta_file: Path = Path(tempfile.gettempdir()) / "filterfusion" / meta_filename
        self.meta_file.parent.mkdir(parents=True, exist_ok=True)
        self.filename_prefix: str = filename_prefix
        self.log_tag: str = log_tag or meta_filename
        self.custom_rules: list[dict[str, Any]] = []

    def load_sources(self) -> list[SourceInfo]:
        """从配置文件加载规则源配置。子类必须实现。"""
        raise NotImplementedError

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名（可加前缀区分不同管道）。"""
        safe_name = self.filename_prefix + name.replace(" ", "_").lower().replace(".", "")
        return f"{safe_name}.txt"

    async def fetch_single_rule(
        self,
        source: SourceInfo,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore | None = None,
    ) -> SourceMeta:
        """异步抓取单个规则源，带 3 次重试与递增超时。

        日志策略：不在开始时打印（避免并发交错），只在完成时打印一行结果。
        重试时静默，仅最终结果输出。

        稳定性优化：
        - semaphore 限制并发请求数，避免触发 GitHub 429 限流
        - 429/503 检测 Retry-After header，优先按服务器要求等待
        - 指数退避叠加 ±25% 随机抖动，避免多源同时重试的惊群效应
        """
        retry_count = 3
        for attempt in range(1, retry_count + 1):
            try:
                # 递增超时：35s → 50s → 65s，适配大型规则文件
                timeout = 20 + attempt * 15
                # 并发上限：semaphore 包裹请求，acquire/release 自动管理
                if semaphore is not None:
                    async with semaphore:
                        response = await client.get(source["url"], timeout=timeout)
                else:
                    response = await client.get(source["url"], timeout=timeout)
                response.raise_for_status()

                # 流式写入：直接写 bytes，避免编码开销
                filename = self._safe_filename(source["name"])
                filepath = self.rules_dir / filename
                filepath.write_bytes(response.content)

                file_hash = hashlib.sha256(response.content).hexdigest()
                timestamp = datetime.now(UTC).isoformat()

                print(f"  ✓ {source['name']}")
                return self._build_success(source, filename, file_hash, timestamp)
            except httpx.TimeoutException:
                if attempt < retry_count:
                    # 指数退避 + ±25% 抖动：1.5^attempt × uniform(0.75, 1.25)
                    base_delay = 1.5 ** attempt
                    await asyncio.sleep(base_delay * random.uniform(0.75, 1.25))
                    continue
                print(f"  ✗ {source['name']} (超时)")
                return self._build_failure(source, "请求超时")
            except httpx.HTTPStatusError as e:
                # 429/503 限流：优先尊重 Retry-After header
                status = e.response.status_code
                if status in (429, 503) and attempt < retry_count:
                    retry_after = self._parse_retry_after(e.response.headers.get("Retry-After"))
                    base_delay = 1.5 ** attempt
                    # 取 Retry-After 与指数退避的较大值，叠加抖动
                    delay = max(retry_after, base_delay) * random.uniform(0.75, 1.25)
                    await asyncio.sleep(delay)
                    continue
                if attempt < retry_count:
                    base_delay = 1.5 ** attempt
                    await asyncio.sleep(base_delay * random.uniform(0.75, 1.25))
                    continue
                print(f"  ✗ {source['name']} (HTTP {status})")
                return self._build_failure(source, f"HTTP {status}")
            except httpx.HTTPError as e:
                if attempt < retry_count:
                    base_delay = 1.5 ** attempt
                    await asyncio.sleep(base_delay * random.uniform(0.75, 1.25))
                    continue
                print(f"  ✗ {source['name']} ({e})")
                return self._build_failure(source, str(e))

        # 理论不可达：循环内已覆盖所有分支返回
        return self._build_failure(source, "重试次数耗尽")

    @staticmethod
    def _parse_retry_after(value: str | None) -> float:
        """解析 Retry-After header，返回等待秒数。

        支持两种格式：
        - 秒数（如 "120"）
        - HTTP date（如 "Wed, 21 Oct 2026 07:28:00 GMT"）
        解析失败返回 0.0（交由调用方回退到指数退避）。
        """
        if not value:
            return 0.0
        # 优先尝试秒数
        try:
            return max(0.0, float(value))
        except ValueError:
            pass
        # 尝试 HTTP date
        try:
            target = parsedate_to_datetime(value)
            if target.tzinfo is None:
                from datetime import timezone

                target = target.replace(tzinfo=timezone.utc)
            delay = (target - datetime.now(UTC)).total_seconds()
            return max(0.0, delay)
        except (TypeError, ValueError):
            return 0.0

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
        if "id" in source:
            result["id"] = source["id"]
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
        if "id" in source:
            result["id"] = source["id"]
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
        if "id" in source:
            result["id"] = source["id"]
        if "category" in source:
            result["category"] = source["category"]
        return result

    async def fetch_all_rules(self) -> dict[str, Any]:
        """并发抓取所有已启用的规则源。

        按 URL 去重：同 URL 只下载一次，下载结果（file/hash/timestamp）
        复制到所有共享该 URL 的 source 记录上。
        """
        sources = self.load_sources()
        results: list[SourceMeta] = []

        print(f"🔍 {self.log_tag}规则源: {len(sources)} 个", flush=True)

        # 分离启用/禁用的源
        enabled_sources = [s for s in sources if s.get("enabled", True)]
        disabled_sources = [s for s in sources if not s.get("enabled", True)]

        # 记录禁用的源
        for source in disabled_sources:
            results.append(self._build_disabled(source))

        # 按 URL 去重：同 URL 只下载一次
        # url -> (首个 source 用于下载, [所有共享该 URL 的 source 索引])
        url_groups: dict[str, list[int]] = {}
        for idx, source in enumerate(enabled_sources):
            url = source["url"]
            url_groups.setdefault(url, []).append(idx)

        # 需要实际下载的源（每组取第一个）
        unique_sources = [enabled_sources[indices[0]] for indices in url_groups.values()]

        # 索引映射：enabled_sources 的位置 -> 下载结果
        download_results: dict[int, SourceMeta] = {}

        print(f"🚀 并发下载 {len(unique_sources)} 个唯一源（去重前 {len(enabled_sources)} 个）...", flush=True)
        if unique_sources:
            # 并发上限：避免源增多时触发 GitHub 429 限流
            semaphore = asyncio.Semaphore(_MAX_CONCURRENT_FETCH)
            async with httpx.AsyncClient(
                http2=True,
                headers={"User-Agent": "FilterFusion/1.0 (+https://github.com/Chaniug/FilterFusion)"},
                follow_redirects=True,
            ) as client:
                # asyncio.gather 原生并发，无线程开销；semaphore 控制实际并发数
                fetched = await asyncio.gather(
                    *(self.fetch_single_rule(s, client, semaphore) for s in unique_sources)
                )

            # 将下载结果映射回所有共享该 URL 的源
            for unique_source, result in zip(unique_sources, fetched, strict=True):
                url = unique_source["url"]
                indices = url_groups[url]
                for idx in indices:
                    src = enabled_sources[idx]
                    if result["status"] == FetchStatus.SUCCESS:
                        # 共享下载结果，但保留各自的 name/id/category
                        shared: SourceMeta = {
                            "name": src["name"],
                            "file": result["file"],
                            "url": src["url"],
                            "timestamp": result["timestamp"],
                            "hash": result["hash"],
                            "status": FetchStatus.SUCCESS,
                        }
                        if "id" in src:
                            shared["id"] = src["id"]
                        if "category" in src:
                            shared["category"] = src["category"]
                        download_results[idx] = shared
                    else:
                        # 失败也共享，但保留各自的 name/id/category
                        failed: SourceMeta = {
                            "name": src["name"],
                            "url": src["url"],
                            "status": result["status"],
                            "error": result.get("error", "未知错误"),
                            "timestamp": result["timestamp"],
                        }
                        if "id" in src:
                            failed["id"] = src["id"]
                        if "category" in src:
                            failed["category"] = src["category"]
                        download_results[idx] = failed

        # 按 enabled_sources 原始顺序组装 results
        for idx, _ in enumerate(enabled_sources):
            results.append(download_results[idx])

        # 保存元数据
        meta: dict[str, Any] = {
            "fetch_date": datetime.now(UTC).isoformat(),
            "sources": results,
        }
        if self.custom_rules:
            meta["custom_rules"] = self.custom_rules
        self.meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        # 统计
        success = sum(1 for s in results if s["status"] == FetchStatus.SUCCESS)
        failed = sum(1 for s in results if s["status"] == FetchStatus.FAILED)

        print(f"✅ {self.log_tag}抓取完成: 成功 {success}, 失败 {failed}")

        return meta
