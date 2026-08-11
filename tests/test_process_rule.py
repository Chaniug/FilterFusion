"""RuleMerger.process_rule() 规则分类边界测试。

纯函数测试：只验证分类逻辑，不触网络、不读写规则文件。
分类优先级参见 merge_rules.py 中 process_rule() 的文档注释。
"""

from __future__ import annotations

import pytest

from scripts.merge_rules import RuleMerger, RuleType


@pytest.fixture(scope="module")
def merger() -> RuleMerger:
    # 实例化只为访问类级预编译正则；dist/ 与 config/ 已存在，mkdir 为 no-op。
    return RuleMerger()


# (输入行, 期望分类)
CASES: list[tuple[str, RuleType | None]] = [
    # --- 1. 注释 (! 或 [) ---
    ("! 这是注释", RuleType.COMMENT),
    ("!Title: x", RuleType.COMMENT),
    ("[Adblock Plus 2.0]", RuleType.COMMENT),
    # --- 2. 例外规则 (@@) ---
    ("@@||example.com^", RuleType.EXCEPTION),
    ("@@||ads.com^$document", RuleType.EXCEPTION),
    # --- 5. 元素隐藏例外 (#@#) 归为例外 ---
    ("example.com#@#.ad-banner", RuleType.EXCEPTION),
    # --- 3. 正则规则 (/pattern/flags) ---
    (r"/banner\d+/", RuleType.REGEX),
    (r"/banner\d+/i", RuleType.REGEX),
    (r"/foo/mg", RuleType.REGEX),
    # // 开头不算正则（避免误伤 URL 协议）→ 普通
    ("//example.com/banner", RuleType.NORMAL),
    # flags 非法（含 x）→ 不算正则，落到普通
    (r"/foo/x", RuleType.NORMAL),
    # --- 4. HTML / 脚本注入 ---
    ("example.com#%#window.x=1", RuleType.HTML_FILTER),
    ("example.com#$#.ad", RuleType.HTML_FILTER),
    ("example.com##+js(abort-current-script)", RuleType.HTML_FILTER),
    ("||ads.com^$removeparam=utm", RuleType.HTML_FILTER),
    # --- 6. 元素隐藏 (##) ---
    ("example.com##.ad", RuleType.ELEMENT_HIDE),
    ("##.ad-block", RuleType.ELEMENT_HIDE),
    # --- 7. 特殊参数 ($ 后) ---
    ("||example.com^$third-party", RuleType.SPECIAL),
    ("||example.com^$badfilter", RuleType.SPECIAL),
    ("||example.com^$domain=foo.com", RuleType.SPECIAL),
    ("||example.com^$important", RuleType.SPECIAL),
    # --- 8. 普通屏蔽 ---
    ("||example.com^", RuleType.NORMAL),
    ("||example.com^$image", RuleType.NORMAL),  # $image 不在特殊参数列表
    ("ads.example.com", RuleType.NORMAL),
    # --- 空行 / 纯空白 ---
    ("", None),
    ("   ", None),
    # --- NFKC 规范化：全角 ！ → 半角 ! 后命中注释 ---
    ("！全角注释", RuleType.COMMENT),
]


@pytest.mark.parametrize("line,expected", CASES)
def test_process_rule_classification(
    merger: RuleMerger, line: str, expected: RuleType | None
) -> None:
    typ, rule = merger.process_rule(line)
    assert typ == expected, f"输入 {line!r} 期望 {expected}，实际 {typ}"
    # 空行返回 (None, None)；非空行 rule 为 strip/NFKC 后的非空字符串
    if expected is None:
        assert rule is None
    else:
        assert rule, f"输入 {line!r} 期望返回非空 rule，实际 {rule!r}"
