import json
import requests
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

class RuleFetcher:
    def __init__(self):
        # 获取项目根目录
        self.project_root = Path(__file__).resolve().parent.parent
        
        # 打印调试信息
        print(f"项目根目录: {self.project_root}")
        
        self.rules_dir = self.project_root / 'rules'
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self.meta_file = self.rules_dir / 'fetch_meta.json'
        
        # 打印调试信息
        print(f"规则目录: {self.rules_dir}")
        
    def load_sources(self):
        try:
            config_path = self.project_root / 'config' / 'sources.json'
            
            # 打印调试信息
            print(f"配置文件路径: {config_path}")
            
            if not config_path.exists():
                print(f"❌ 错误：找不到配置文件 {config_path}")
                sys.exit(1)
                
            with open(config_path, 'r') as f:
                data = json.load(f)
                print(f"加载了 {len(data['sources'])} 个规则源")
                return data['sources']
        except FileNotFoundError:
            print("❌ 错误：找不到 sources.json 配置文件")
            sys.exit(1)
        except json.JSONDecodeError:
            print("❌ 错误：sources.json 配置格式不正确")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 加载配置文件时出错: {str(e)}")
            sys.exit(1)
    
    def fetch_single_rule(self, source):
        retry_count = 3
        for attempt in range(1, retry_count + 1):
            try:
                print(f"⬇️  抓取规则: {source['name']} (尝试 {attempt}/{retry_count})...", end=' ', flush=True)
                # 增加超时时间
                timeout = 10 + attempt * 5
                response = requests.get(source['url'], timeout=timeout)
                response.raise_for_status()
                
                # 生成安全的文件名
                safe_name = source['name'].replace(' ', '_').lower().replace('.', '')
                filename = f"{safe_name}.txt"
                filepath = self.rules_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                file_hash = hashlib.sha256(response.content).hexdigest()
                timestamp = datetime.now(timezone.utc).isoformat()
                
                print("✓")
                return {
                    "name": source['name'],
                    "file": filename,
                    "url": source['url'],
                    "timestamp": timestamp,
                    "hash": file_hash,
                    "status": "success"
                }
            except requests.exceptions.Timeout:
                if attempt < retry_count:
                    print("超时，重试...", end=' ')
                else:
                    print("✗ (超时)")
                    return {
                        "name": source['name'],
                        "url": source['url'],
                        "status": "failed",
                        "error": "请求超时",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
            except requests.exceptions.RequestException as e:
                if attempt < retry_count:
                    print(f"错误 ({str(e)}), 重试...", end=' ')
                else:
                    print(f"✗ ({str(e)})")
                    return {
                        "name": source['name'],
                        "url": source['url'],
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
    
    def fetch_all_rules(self):
        sources = self.load_sources()
        results = []
        
        print("\n" + "="*50)
        print("🔍 开始抓取广告过滤规则...")
        print(f"📡 共检测到 {len(sources)} 个规则源")
        print("="*50)
        
        for source in sources:
            if not source.get('enabled', True):
                print(f"⏭️  跳过禁用规则: {source['name']}")
                continue
            result = self.fetch_single_rule(source)
            results.append(result)
        
        # 保存元数据
        meta = {
            "fetch_date": datetime.now(timezone.utc).isoformat(),
            "sources": results
        }
        
        with open(self.meta_file, 'w') as f:
            json.dump(meta, f, indent=2)
        
        # 计算统计信息
        success = sum(1 for s in results if s['status'] == 'success')
        failed = sum(1 for s in results if s['status'] == 'failed')
        
        print("\n" + "="*50)
        print(f"✅ 抓取完成: 成功 {success} 个, 失败 {failed} 个")
        print("="*50)
        
        if failed > 0:
            print("\n失败的来源:")
            for source in results:
                if source['status'] == 'failed':
                    print(f"  - {source['name']}: {source.get('error', '未知错误')}")
        
        print(f"抓取元数据已保存至: {self.meta_file}")
        return meta

if __name__ == "__main__":
    print("="*50)
    print("🚀 FilterFusion - 广告规则抓取工具")
    print("="*50)
    
    fetcher = RuleFetcher()
    try:
        metadata = fetcher.fetch_all_rules()
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)