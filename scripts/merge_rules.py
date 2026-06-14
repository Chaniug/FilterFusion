import json
import hashlib
import sys
import shutil
import unicodedata
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class RuleMerger:
    def __init__(self) -> None:
        # 获取项目根目录
        self.project_root: Path = Path(__file__).resolve().parent.parent
        print(f"项目根目录: {self.project_root}")

        self.dist_dir: Path = self.project_root / 'dist'
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir: Path = self.project_root / 'rules'

        print(f"分发目录: {self.dist_dir}")
        print(f"规则目录: {self.rules_dir}")

        # 统计信息
        self.initial_rule_count: int = 0
        self.final_rule_count: int = 0
        self.start_time: datetime = datetime.now()

    def load_metadata(self) -> dict[str, Any]:
        # 获取元数据文件路径
        meta_path = self.rules_dir / 'fetch_meta.json'
        print(f"尝试加载元数据: {meta_path}")

        if not meta_path.exists():
            print(f"❌ 错误：找不到抓取元数据文件 {meta_path}")
            sys.exit(1)

        try:
            with open(meta_path, 'r') as f:
                print("成功加载元数据文件")
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ 错误：元数据文件格式不正确 {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 加载元数据时出错: {str(e)}")
            sys.exit(1)

    def load_header_template(self) -> str:
        # 获取头部模板路径
        header_path = self.project_root / 'config' / 'default.header'
        print(f"尝试加载头部模板: {header_path}")

        if not header_path.exists():
            print(f"❌ 错误：找不到头部模板 {header_path}")
            print("请确保文件存在:")
            print(f"位置: {header_path}")
            print("文件内容应为:")
            print("-" * 50)
            print('''! Title: FilterFusion AdBlock Rules
! Version: {VERSION}
! Updated: {TIMEUPDATED}
! Last modified: {TIMEUPDATED}
! Checksum: {CHECKSUM}
! Homepage: {HOMEPAGE}
! Expires: 1 day
! License: {LICENSE}''')
            print("-" * 50)
            sys.exit(1)

        try:
            with open(header_path, 'r') as f:
                print("成功加载头部模板")
                return f.read()
        except Exception as e:
            print(f"❌ 读取头部模板失败: {str(e)}")
            sys.exit(1)

    def generate_source_list(self, sources: list[dict[str, Any]]) -> str:
        """生成格式化的源列表信息"""
        source_info = []
        for source in sources:
            status_icon = "✓" if source.get('status') == 'success' else "✗"
            source_info.append(f"! - {status_icon} {source['name']} (更新: {source['timestamp'][:10]})")
        return "\n".join(source_info)

    def process_rule(self, line: str) -> tuple[str | None, str | None]:
        """
        对单条规则进行规范化、分组和兼容性处理，返回 (type, rule)。
        type: normal/exception/html_filter/regex/special/comment/element_hide

        规则分类优先级（符合 AdGuard/ABP/uBlock 标准）:
        1. 注释 (! 或 [Adblock Plus])
        2. 例外规则 (@@)
        3. 正则规则 (/pattern/flags)
        4. HTML/脚本注入规则 (#%#, #$#, scriptlet 等)
        5. 元素隐藏规则 (##, #@#)
        6. 特殊参数规则 ($badfilter, $important 等)
        7. 普通屏蔽规则
        """
        # 去除不可见字符和多余空白
        rule = unicodedata.normalize('NFKC', line.strip())
        if not rule:
            return (None, None)

        # 1. 注释规则
        # Adblock Plus 标准: ! 或 # 开头的注释（不含规则指令）
        # 排除：##, #@#, #%#, #$#, #?#, #+# 等规则指令
        if rule.startswith('!') or rule.startswith('['):
            return ('comment', rule)

        # 2. 例外规则 (@@) - 最高优先级（例外规则可能包含其他语法）
        if rule.startswith('@@'):
            return ('exception', rule)

        # 3. 正则规则 (Adblock Plus 格式: /pattern/flags)
        # 标准: 以 / 开头，以 / 结尾，中间是正则模式，尾部可有标志 (i, g, m)
        if rule.startswith('/') and not rule.startswith('//'):
            # 找到最后一个 / 的位置（分隔模式和标志）
            last_slash = rule.rfind('/')
            if last_slash > 0:  # 确保不是第一个字符（已有 startswith('/') 保证）
                # 检查尾部标志是否有效（Adblock 支持 i, g, m）
                flags = rule[last_slash + 1:]
                if all(c in 'igm' for c in flags) or not flags:
                    # 基本验证：确保不是简单的路径（如 /ads.html）
                    # 正则规则的特征：包含正则特殊字符 或 长度 > 10（经验值）
                    pattern = rule[1:last_slash]
                    has_regex_chars = any(c in pattern for c in ['.', '*', '+', '?', '\\', '[', ']', '(', ')', '{', '}', '^', '$', '|'])
                    if has_regex_chars or len(pattern) > 15:  # 放松限制，避免误判
                        return ('regex', rule)

        # 4. AdGuard/uBlock 扩展语法（必须在元素隐藏之前判断）
        # 这些规则包含特殊指令，不应被识别为普通元素隐藏
        html_filter_keywords = [
            "#%#", "#@%#",      # AdGuard JS 注入
            "#$#", "#@$#",      # AdGuard CSS 注入
            "#?#", "#@?#",      # AdGuard 元素筛选
            "#+js(", "#@#+js(", # uBlock scriptlet
            "$removeparam",       # uBlock 参数移除
            "$cookie=",           # AdGuard cookie 管理
            "$redirect=",         # AdGuard 资源重定向
            "$generichide",      # AdGuard 通用隐藏
            "scriptlet(",         # AdGuard scriptlet
            "jsinject"           # 旧版 JS 注入
        ]
        if any(k in rule for k in html_filter_keywords):
            return ('html_filter', rule)

        # 5. 元素隐藏规则
        # 标准: domain##selector 或 ##selector（全局隐藏）
        # 例外: @@## 不是元素隐藏，已在第 2 步处理
        if '##' in rule:
            return ('element_hide', rule)

        # 6. 特殊参数规则（更严格的判断：确保在选项部分）
        # 标准: 选项部分以 $ 开头，包含修饰符
        if '$' in rule:
            # 提取选项部分（第一个 $ 之后的内容）
            option_part = rule.split('$', 1)[1]
            special_keywords = [
                'badfilter',     # 禁用规则
                'important',     # 高优先级
                'app=',          # AdGuard 应用过滤
                'domain=',       # 域名限定
                'csp=',          # 内容安全策略
                'replace=',      # URL 替换
                'popup',         # 弹窗拦截
                'third-party'    # 第三方请求
            ]
            if any(kw in option_part for kw in special_keywords):
                return ('special', rule)

        # 7. 普通屏蔽规则
        # 标准: ||domain^, |http://..., *ad.* 等
        return ('normal', rule)

    def collect_and_process_rules(self, sources: list[dict[str, Any]]) -> tuple[list[str], dict[str, set[str]], list[dict[str, Any]]]:
        """
        收集并处理规则，语法分组、格式规范、扩展兼容，同时统计每个源的规则数
        返回: merged_lines, groups, source_stats
        """
        # 分组容器
        groups = {
            'normal': set(),
            'exception': set(),
            'element_hide': set(),
            'html_filter': set(),
            'regex': set(),
            'special': set(),
            'comment': set()
        }
        seen_rules = set()
        source_stats = []
        print("收集和处理规则:")
        for source in sources:
            if source.get('status') != 'success':
                continue
            source_path = self.rules_dir / source['file']
            print(f"处理源文件: {source_path}")
            if not source_path.exists():
                continue
            source_rule_count = 0
            source_seen = set()  # 源内去重（独立于全局）
            try:
                with open(source_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        typ, rule = self.process_rule(line)
                        if not typ or not rule:
                            continue
                        # 注释只保留前10条
                        if typ == 'comment':
                            if rule not in groups['comment'] and len(groups['comment']) < 10:
                                groups['comment'].add(rule)
                            continue
                        # 源内去重计数
                        rule_id = f"{typ}:{rule}"
                        if rule_id in source_seen:
                            continue
                        source_seen.add(rule_id)
                        source_rule_count += 1
                        # 全局去重
                        if rule_id in seen_rules:
                            continue
                        seen_rules.add(rule_id)
                        groups[typ].add(rule)
            except Exception as e:
                print(f"⚠️ 警告：处理 {source['name']} 规则时出错: {str(e)}")
            print(f"源 {source['name']} 有效规则数: {source_rule_count}")
            source_stats.append({
                "name": source['name'],
                "rule_count": source_rule_count
            })

        # 输出时按分组分类拼接（去掉注释分组）
        merged_lines = []
        # 注释分组已去除不输出
        if groups['exception']:
            merged_lines.append("! === 例外规则 Exception Rules ===")
            merged_lines.extend(sorted(groups['exception']))
            merged_lines.append("")
        if groups['element_hide']:
            merged_lines.append("! === 元素隐藏规则 Element Hiding Rules ===")
            merged_lines.extend(sorted(groups['element_hide']))
            merged_lines.append("")
        if groups['html_filter']:
            merged_lines.append("! === AdGuard/HTML Scriptlet Rules ===")
            merged_lines.extend(sorted(groups['html_filter']))
            merged_lines.append("")
        if groups['regex']:
            merged_lines.append("! === 正则规则 Regex Rules ===")
            merged_lines.extend(sorted(groups['regex']))
            merged_lines.append("")
        if groups['special']:
            merged_lines.append("! === 特殊参数/实验性规则 Special/Experimental ===")
            merged_lines.extend(sorted(groups['special']))
            merged_lines.append("")
        if groups['normal']:
            merged_lines.append("! === 屏蔽规则 Blocking Rules ===")
            merged_lines.extend(sorted(groups['normal']))
            merged_lines.append("")

        print(f"收集了 {sum(len(v) for k, v in groups.items() if k != 'comment')} 条唯一规则")
        return merged_lines, groups, source_stats

    def generate_version(self) -> str:
        """生成简单的语义化版本号"""
        today = datetime.now(timezone.utc)
        return f"{today.year}{today.month:02d}{today.day:02d}"

    def merge(self) -> None:
        print("="*50)
        print("🔧 FilterFusion - 广告规则合并工具")
        print("="*50)

        # 加载数据
        print("步骤1: 加载元数据")
        metadata = self.load_metadata()
        sources = metadata['sources']

        # 检查是否有成功抓取的源
        success_sources = [s for s in sources if s.get('status') == 'success']
        if not success_sources:
            print("❌ 错误：没有成功抓取的规则源，终止合并")
            sys.exit(1)

        print("步骤2: 加载头部模板")
        header_template = self.load_header_template()

        print("步骤3: 收集、处理和去重规则")
        rules, groups, source_stats = self.collect_and_process_rules(sources)
        self.initial_rule_count = sum(s['rule_count'] for s in source_stats)
        self.final_rule_count = sum(len(v) for k, v in groups.items() if k != 'comment')

        print("步骤4: 生成版本号")
        version = self.generate_version()

        print("步骤5: 生成头部")
        source_list = self.generate_source_list(sources)
        header = header_template \
            .replace('{VERSION}', version) \
            .replace('{TIMEUPDATED}', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')) \
            .replace('{TIMEUPDATED_ISO}', datetime.now(timezone.utc).isoformat()) \
            .replace('{SOURCE_COUNT}', str(len([s for s in sources if s.get('status') == 'success']))) \
            .replace('{SOURCE_LIST}', source_list) \
            .replace('{COMBINED_RULES}', str(self.final_rule_count)) \
            .replace('{TOTAL_RULES}', str(self.initial_rule_count)) \
            .replace('{DUPLICATES}', str(self.initial_rule_count - self.final_rule_count)) \
            .replace('{HOMEPAGE}', "https://github.com/Chaniug/FilterFusion") \
            .replace('{LICENSE}', "MIT License")

        # 构建最终内容
        content = header.rstrip("\n") + "\n" + "\n".join(rules)

        # 计算校验和（ABP 标准：MD5 + Base64）
        print("步骤6: 计算校验和（ABP 标准）")
        content_for_checksum = "\n".join(
            line for line in content.split("\n")
            if not line.startswith("! Checksum:")
        )
        md5_hash = hashlib.md5(content_for_checksum.encode('utf-8')).digest()
        checksum = base64.b64encode(md5_hash).decode('utf-8')
        content = content.replace('{CHECKSUM}', checksum)

        # 保存前检查规则数是否为0
        if self.final_rule_count == 0:
            print("⚠️ 警告：合并后规则数为 0，不覆盖现有文件")
            return

        # 保存规则文件
        rule_filename = f"adblock-{version}.txt"
        rule_path = self.dist_dir / rule_filename
        print(f"保存规则文件到: {rule_path}")
        with open(rule_path, 'w', encoding='utf-8') as f:
            _ = f.write(content)

        # 保存最新规则副本（最佳实践：直接复制内容而非符号链接）
        print("步骤7: 保存最新规则副本")
        main_path = self.dist_dir / "adblock-main.txt"
        if main_path.exists():
            main_path.unlink()
        shutil.copyfile(rule_path, main_path)  # 直接复制文件内容
        _ = main_path.exists()  # 触发 Path 类型表达式

        # 计算处理时间
        processing_time = (datetime.now() - self.start_time).total_seconds()

        # 显示摘要
        print("\n" + "="*50)
        print("✅ 规则合并完成!")
        print("="*50)
        print(f"🔖 版本: {version}")
        print(f"📦 源规则数量: {self.initial_rule_count}")
        print(f"🪄 合并后规则数量: {self.final_rule_count}")
        print(f"♻️  重复规则: {self.initial_rule_count - self.final_rule_count}")
        print(f"⏱️  处理时间: {processing_time:.2f}秒")
        print(f"🔐 校验和: {checksum}")
        print(f"📄 合并规则文件: dist/{rule_filename}")
        print(f"📄 最新规则副本: dist/adblock-main.txt")

        # 保存摘要信息
        print("步骤8: 保存摘要信息")
        self.save_summary(version, checksum, source_stats, processing_time)

    def save_summary(self, version: str, checksum: str, source_stats: list[dict[str, Any]], processing_time: float) -> None:
        """保存摘要信息到 JSON 文件"""
        summary = {
            "version": version,
            "date": datetime.now(timezone.utc).isoformat(),
            "total_source_rules": self.initial_rule_count,
            "unique_rules": self.final_rule_count,
            "duplicates_removed": self.initial_rule_count - self.final_rule_count,
            "merge_time_seconds": round(processing_time, 2),
            "checksum": checksum,
            "sources": source_stats
        }

        summary_path = self.dist_dir / "summary.json"
        print(f"保存摘要到: {summary_path}")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"📊 摘要信息已保存至: dist/summary.json")

if __name__ == "__main__":
    merger = RuleMerger()
    try:
        merger.merge()
    except Exception as e:
        print(f"❌ 合并过程中发生致命错误: {str(e)}")
        sys.exit(1)
