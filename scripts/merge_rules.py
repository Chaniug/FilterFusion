import json
import hashlib
import sys
import shutil
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

class RuleMerger:
    def __init__(self):
        # 获取项目根目录
        self.project_root = Path(__file__).resolve().parent.parent
        print(f"项目根目录: {self.project_root}")

        self.dist_dir = self.project_root / 'dist'
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir = self.project_root / 'rules'

        print(f"分发目录: {self.dist_dir}")
        print(f"规则目录: {self.rules_dir}")

        # 统计信息
        self.initial_rule_count = 0
        self.final_rule_count = 0
        self.start_time = datetime.now()

    def load_metadata(self):
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

    def load_header_template(self):
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

    def generate_source_list(self, sources):
        """生成格式化的源列表信息"""
        source_info = []
        for source in sources:
            status_icon = "✓" if source.get('status') == 'success' else "✗"
            source_info.append(f"! - {status_icon} {source['name']} (更新: {source['timestamp'][:10]})")
        return "\n".join(source_info)

    def calculate_source_stats(self, sources):
        """计算源规则统计数据"""
        source_stats = []
        rule_counts = defaultdict(int)

        print("计算源规则统计:")
        for source in sources:
            if source.get('status') != 'success':
                continue

            source_path = self.rules_dir / source['file']
            print(f"处理源: {source['name']}")
            print(f"文件路径: {source_path}")

            if not source_path.exists():
                print(f"文件不存在: {source_path}")
                continue

            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    rule_count = 0
                    for line in f:
                        stripped = line.strip()
                        if stripped and not stripped.startswith(('!', '#', '[Adblock')):
                            rule_count += 1
                    print(f"源 {source['name']} 规则数: {rule_count}")
                    source_stats.append({
                        "name": source['name'],
                        "rule_count": rule_count
                    })
                    rule_counts[source['name']] = rule_count
            except UnicodeDecodeError:
                print(f"⚠️ 警告：规则文件 {source['file']} 编码问题")
                source_stats.append({
                    "name": source['name'],
                    "rule_count": 0
                })

        print("源统计完成")
        return source_stats, rule_counts

    def process_rule(self, line):
        """
        对单条规则进行规范化、分组和兼容性处理，返回 (type, rule)。
        type: normal/exception/html_filter/regex/special/comment
        """
        # 去除不可见字符和多余空白
        rule = unicodedata.normalize('NFKC', line.strip())
        if not rule:
            return (None, None)
        # 注释
        if rule.startswith('!') or rule.startswith('#'):
            return ('comment', rule)
        # 正则 (如 /adunion.*/ 或 /xxx/[flags])
        if re.match(r"^\/.+\/[a-zA-Z0-9]*$", rule):
            return ('regex', rule)
        # AdGuard扩展语法/HTML/scriptlet等
        if any(k in rule for k in [
            "#%#", "#@#", "#$#", "#@$#", "#?#",
            "$removeparam=", "$cookie=", "$redirect=",
            "$generichide", "scriptlet(", "jsinject"
        ]):
            return ('html_filter', rule)
        # 例外规则 (@@)
        if rule.startswith('@@'):
            return ('exception', rule)
        # uBlock/AdGuard特殊参数
        if any(k in rule for k in [
            "$badfilter", "$important", "$app=", "$domain=", "$csp=", "$replace="
        ]):
            return ('special', rule)
        # 普通屏蔽
        return ('normal', rule)

    def collect_and_process_rules(self, sources, rule_counts):
        """
        收集并处理规则，语法分组、格式规范、扩展兼容
        返回: merged_lines, groups
        """
        # 分组容器
        groups = {
            'normal': set(),
            'exception': set(),
            'html_filter': set(),
            'regex': set(),
            'special': set(),
            'comment': set()
        }
        seen_rules = set()
        print("收集和处理规则:")
        for source in sources:
            if source.get('status') != 'success' or rule_counts.get(source['name'], 0) == 0:
                continue
            source_path = self.rules_dir / source['file']
            print(f"处理源文件: {source_path}")
            if not source_path.exists():
                continue
            try:
                with open(source_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        typ, rule = self.process_rule(line)
                        if not rule or (typ == 'comment' and rule in groups['comment']):
                            continue
                        # 注释只保留前10条
                        if typ == 'comment':
                            if len(groups['comment']) < 10:
                                groups['comment'].add(rule)
                            continue
                        # 其余类型做全局唯一去重
                        rule_id = f"{typ}:{rule}"
                        if rule_id in seen_rules:
                            continue
                        seen_rules.add(rule_id)
                        groups[typ].add(rule)
            except Exception as e:
                print(f"⚠️ 警告：处理 {source['name']} 规则时出错: {str(e)}")

        # 输出时按分组分类拼接（去掉注释分组）
        merged_lines = []
        # 注释分组已去除不输出
        if groups['exception']:
            merged_lines.append("! === 例外规则 Exception Rules ===")
            merged_lines.extend(sorted(groups['exception']))
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
        return merged_lines, groups

    def generate_version(self):
        """生成简单的语义化版本号"""
        today = datetime.now(timezone.utc)
        return f"{today.year}{today.month:02d}{today.day:02d}"

    def merge(self):
        print("="*50)
        print("🔧 FilterFusion - 广告规则合并工具")
        print("="*50)

        # 加载数据
        print("步骤1: 加载元数据")
        metadata = self.load_metadata()
        sources = metadata['sources']

        print("步骤2: 加载头部模板")
        header_template = self.load_header_template()

        print("步骤3: 计算源规则统计")
        source_stats, rule_counts = self.calculate_source_stats(sources)
        self.initial_rule_count = sum(rule_counts.values())

        print("步骤4: 收集和处理规则")
        rules, groups = self.collect_and_process_rules(sources, rule_counts)
        self.final_rule_count = sum(len(v) for k, v in groups.items() if k != 'comment')

        print("步骤5: 生成版本号")
        version = self.generate_version()

        print("步骤6: 生成头部")
        source_list = self.generate_source_list(sources)
        header = header_template \
            .replace('{VERSION}', version) \
            .replace('{TIMEUPDATED}', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')) \
            .replace('{SOURCE_COUNT}', str(len([s for s in sources if s.get('status') == 'success']))) \
            .replace('{SOURCE_LIST}', source_list) \
            .replace('{RULE_COUNT}', str(self.final_rule_count)) \
            .replace('{HOMEPAGE}', "https://github.com/Chaniug/FilterFusion") \
            .replace('{LICENSE}', "MIT License")

        # 构建最终内容
        content = header
        content += f"! Combined rules: {self.final_rule_count}\n"
        content += f"! Total rules: {self.initial_rule_count}\n"
        content += f"! Repetitions: {self.initial_rule_count - self.final_rule_count}\n\n"
        content += "\n".join(rules)

        # 计算校验和
        print("步骤7: 计算校验和")
        checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        content = content.replace('{CHECKSUM}', checksum)

        # 保存规则文件
        rule_filename = f"adblock-{version}.txt"
        rule_path = self.dist_dir / rule_filename
        print(f"保存规则文件到: {rule_path}")
        with open(rule_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 保存最新规则副本（最佳实践：直接复制内容而非符号链接）
        print("步骤8: 保存最新规则副本")
        main_path = self.dist_dir / "adblock-main.txt"
        if main_path.exists():
            main_path.unlink()
        shutil.copyfile(rule_path, main_path)  # 直接复制文件内容

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
        print(f"🔐 校验和: {checksum[:16]}...{checksum[-16:]}")
        print(f"📄 合并规则文件: dist/{rule_filename}")
        print(f"📄 最新规则副本: dist/adblock-main.txt")

        # 保存摘要信息
        print("步骤9: 保存摘要信息")
        self.save_summary(version, checksum, source_stats, processing_time)

    def save_summary(self, version, checksum, source_stats, processing_time):
        """保存摘要信息到 JSON 文件"""
        summary = {
            "date": datetime.now(timezone.utc).isoformat(),
            "version": version,
            "sources": source_stats,
            "stats": {
                "initial_rules": self.initial_rule_count,
                "final_rules": self.final_rule_count,
                "duplicates": self.initial_rule_count - self.final_rule_count,
                "processing_time_sec": processing_time,
                "checksum": checksum
            }
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
