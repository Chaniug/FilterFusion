"""FilterFusion AdBlock 规则抓取模块 — 基于 httpx 异步客户端 + HTTP/2 多路复用。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.base_fetcher import BaseFetcher, SourceInfo

# YAML 配置中的 category 缩写 → 内部全称（同时兼容旧全称写法）
# 内部元数据（fetch_meta.json）统一存储全称，下游脚本无需改动
CATEGORY_MAP: dict[str, str] = {
    "mo": "mobile",
    "pc": "pc",
    "bo": "both",
    "mobile": "mobile",   # 兼容旧写法
    "both": "both",       # 兼容旧写法
}


class RuleFetcher(BaseFetcher):
    """异步抓取多源广告过滤规则。

    使用 httpx.AsyncClient 单例，HTTP/2 多路复用，复用 TLS 连接。
    """

    def __init__(self) -> None:
        super().__init__(meta_filename="fetch_meta.json", filename_prefix="", log_tag="广告")

    def load_sources(self) -> list[SourceInfo]:
        """从 config/sources.yaml 加载规则源配置。

        YAML 格式（字段顺序可任意，name 建议放首位便于阅读）:
          sources:
            - name: AdGuard Mobile
              category: mo / pc / bo      # 缩写，也兼容旧全称 mobile/pc/both
              url: https://...
              id: m1                       # 唯一短编号，被 custom_rules 按 ID 引用
          custom_rules:
            - output: adblock-mo.txt
              description: FilterFusion - Ad blocking rules (Mobile)  # 可选
              sources: [m1, m2, m3, b1, b2]

        category 取值（缩写优先，兼容全称）:
          mo / mobile  — 手机端
          pc           — 电脑端
          bo / both    — 两端共用，展开为 mobile + pc 两条记录（URL 相同，去重下载）
        """
        config_path = self.project_root / "config" / "sources.yaml"

        if not config_path.exists():
            print(f"❌ 找不到配置文件 {config_path}")
            sys.exit(1)

        sources: list[SourceInfo] = []
        seen_ids: set[str] = set()

        try:
            data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            print(f"❌ YAML 解析失败: {e}")
            sys.exit(1)

        # 解析 sources 段
        raw_sources = data.get("sources") or []
        for idx, item in enumerate(raw_sources, 1):
            source_id = str(item.get("id", "")).strip()
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()
            raw_category = str(item.get("category", "mobile")).strip().lower()
            category = CATEGORY_MAP.get(raw_category, "")

            if not name or not url:
                print(f"⚠️ 第 {idx} 个源缺少 name 或 url，跳过")
                continue

            if not url.startswith("http"):
                print(f"⚠️ 第 {idx} 个源 url 无效: {url}")
                continue

            if not category:
                print(f"⚠️ 第 {idx} 个源 category 无效 '{raw_category}'（应为 mo/pc/bo），默认为 mobile")
                category = "mobile"

            # both 展开为 mobile + pc 两条记录（URL 相同，fetch 阶段按 URL 去重）
            if category == "both":
                targets = ["mobile", "pc"]
            else:
                targets = [category]

            for cat in targets:
                record: SourceInfo = {
                    "name": name,
                    "url": url,
                    "category": cat,
                    "enabled": True,
                }
                if source_id:
                    # both 源两条记录共享同一 id（用于组合规则按 ID 引用）
                    if source_id in seen_ids and cat == targets[0]:
                        print(f"⚠️ 重复的源 ID '{source_id}'，跳过")
                        break
                    if source_id not in seen_ids:
                        seen_ids.add(source_id)
                    record["id"] = source_id
                sources.append(record)

            # 同时记录用于组合规则的 id → name/url 映射（仅首次出现时）

        # 解析 custom_rules 段
        raw_custom = data.get("custom_rules") or []
        for item in raw_custom:
            output = str(item.get("output", "")).strip()
            rule_sources = item.get("sources") or []
            description = str(item.get("description", "")).strip()
            if not output or not rule_sources:
                print(f"⚠️ 组合规则缺少 output 或 sources，跳过")
                continue

            # 规范化 source_ids 为字符串列表
            source_ids = [str(s).strip() for s in rule_sources if str(s).strip()]
            if not source_ids:
                print(f"⚠️ 组合规则 '{output}' 的 sources 为空，跳过")
                continue

            rule_config: dict[str, Any] = {
                "output": output,
                "sources": source_ids,
            }
            if description:
                rule_config["description"] = description
            self.custom_rules.append(rule_config)

        print(f"加载了 {len(sources)} 个规则源，{len(self.custom_rules)} 个组合规则")
        return sources


async def main() -> None:
    fetcher = RuleFetcher()
    try:
        await fetcher.fetch_all_rules()
    except Exception as e:
        print(f"\n❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
