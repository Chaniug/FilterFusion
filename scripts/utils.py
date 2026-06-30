"""FilterFusion 公共工具模块 — 跨脚本复用的纯函数与基类。"""

from __future__ import annotations

from datetime import UTC, datetime


def generate_version() -> str:
    """生成版本号（YYYYMMDDHHMM，UTC 精确到分钟，可区分当天多次提交）。"""
    now = datetime.now(UTC)
    return f"{now.year}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute:02d}"
