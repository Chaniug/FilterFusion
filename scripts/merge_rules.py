import json
import hashlib
import sys
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
    
    def collect_and_process_rules(self, sources, rule_counts):
        """收集并处理规则"""
        all_rules = []
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
                        stripped = line.strip()
                        # 跳过空行和注释
                        if not stripped or stripped.startswith('!') or stripped.startswith('#'):
                            continue
                            
                        # 简单去重
                        if stripped in seen_rules:
                            continue
                            
                        seen_rules.add(stripped)
                        all_rules.append(stripped)
            except Exception as e:
                print(f"⚠️ 警告：处理 {source['name']} 规则时出错: {str(e)}")
        
        print(f"收集了 {len(all_rules)} 条唯一规则")
        return all_rules
    
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
        rules = self.collect_and_process_rules(sources, rule_counts)
        self.final_rule_count = len(rules)
        
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
        content = header + "\n\n"
        content += f"! 合并规则数量: {self.final_rule_count}\n"
        content += f"! 源规则总数: {self.initial_rule_count}\n"
        content += f"! 重复规则: {self.initial_rule_count - self.final_rule_count}\n\n"
        content += "\n".join(rules)
        
        # 计算校验和
        print("步骤7: 计算校验和")
        checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        content = content.replace('{CHECKSUM}', checksum)
        
        # 保存规则文件
        rule_filename = f"adblockfile.txt"
        rule_path = self.dist_dir / rule_filename
        print(f"保存规则文件到: {rule_path}")
        with open(rule_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 创建符号链接
        print("步骤8: 创建符号链接")
        latest_path = self.dist_dir / "adblock-latest.txt"
        if latest_path.exists() or latest_path.is_symlink():
            latest_path.unlink()
        latest_path.symlink_to(rule_filename)
        
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
        print(f"🔗 最新规则链接: dist/adblock-latest.txt")
        
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
        