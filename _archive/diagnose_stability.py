#!/usr/bin/env python3
"""
服务器稳定性诊断工具
用于监控文件变化和识别导致 Streamlit 重载的原因
"""

import os
import time
import hashlib
from pathlib import Path
from datetime import datetime

class FileChangeMonitor:
    def __init__(self, watch_dir="."):
        self.watch_dir = Path(watch_dir)
        self.ignore_patterns = [
            'venv', '__pycache__', '.git', '.pytest_cache',
            '*.pyc', '*.pyo', '*.log', '.steamlit'
        ]
        self.file_hashes = {}
        
    def should_ignore(self, path):
        """检查路径是否应该被忽略"""
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern in path_str or path_str.endswith(pattern.replace('*', '')):
                return True
        return False
    
    def get_file_hash(self, filepath):
        """获取文件的 MD5 哈希"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def scan_files(self):
        """扫描所有 Python 文件"""
        python_files = []
        for root, dirs, files in os.walk(self.watch_dir):
            # 过滤目录
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    if not self.should_ignore(filepath):
                        python_files.append(filepath)
        return python_files
    
    def detect_changes(self):
        """检测文件变化"""
        changes = []
        current_files = self.scan_files()
        current_hashes = {}
        
        # 检查修改和新增
        for filepath in current_files:
            current_hash = self.get_file_hash(filepath)
            current_hashes[filepath] = current_hash
            
            if filepath not in self.file_hashes:
                changes.append(('NEW', filepath))
            elif self.file_hashes[filepath] != current_hash:
                changes.append(('MODIFIED', filepath))
        
        # 检查删除
        for filepath in self.file_hashes:
            if filepath not in current_hashes:
                changes.append(('DELETED', filepath))
        
        self.file_hashes = current_hashes
        return changes
    
    def monitor(self, interval=2):
        """持续监控文件变化"""
        print("🔍 开始监控文件变化...")
        print(f"📁 监控目录: {self.watch_dir.absolute()}")
        print(f"⏱️  检查间隔: {interval} 秒")
        print(f"🚫 忽略模式: {', '.join(self.ignore_patterns)}")
        print("\n初始化扫描...\n")
        
        # 初始扫描
        self.detect_changes()
        print(f"✅ 找到 {len(self.file_hashes)} 个 Python 文件\n")
        print("="*60)
        print("开始监控（Ctrl+C 停止）...")
        print("="*60)
        
        change_count = 0
        try:
            while True:
                time.sleep(interval)
                changes = self.detect_changes()
                
                if changes:
                    change_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n[{timestamp}] 检测到 {len(changes)} 个文件变化：")
                    
                    for change_type, filepath in changes:
                        rel_path = filepath.relative_to(self.watch_dir)
                        emoji = "📝" if change_type == "MODIFIED" else "➕" if change_type == "NEW" else "❌"
                        print(f"  {emoji} {change_type:8} {rel_path}")
                    
                    print(f"\n💡 这可能导致 Streamlit 重载！（总计: {change_count} 次变化）")
                    print("-"*60)
        
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print(f"✋ 监控停止。总共检测到 {change_count} 次变化。")
            print("="*60)


def check_frequent_writes():
    """检查频繁写入的文件"""
    print("\n🔎 检查最近频繁修改的文件...\n")
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("⚠️  data/ 目录不存在")
        return
    
    recent_files = []
    now = time.time()
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            filepath = Path(root) / file
            try:
                mtime = filepath.stat().st_mtime
                age = now - mtime
                if age < 300:  # 最近 5 分钟修改的
                    recent_files.append((filepath, age))
            except:
                pass
    
    recent_files.sort(key=lambda x: x[1])
    
    if recent_files:
        print(f"📊 最近 5 分钟内修改的文件 ({len(recent_files)} 个)：\n")
        for filepath, age in recent_files[:20]:
            mins = int(age / 60)
            secs = int(age % 60)
            print(f"  • {filepath} ({mins}分{secs}秒前)")
    else:
        print("✅ 未发现最近修改的数据文件")


def analyze_config():
    """分析当前配置"""
    print("\n⚙️  分析 Streamlit 配置...\n")
    
    config_path = Path(".streamlit/config.toml")
    if config_path.exists():
        print(f"✅ 找到配置文件: {config_path}")
        with open(config_path) as f:
            content = f.read()
            if "fileWatcherType" in content:
                print("  ✓ 已设置文件监控类型")
            if "runOnSave" in content:
                print("  ✓ 已设置热重载选项")
    else:
        print(f"⚠️  未找到配置文件: {config_path}")
        print("  建议创建配置文件来优化文件监控行为")


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("🔮 AI Bazi 服务器稳定性诊断工具")
    print("="*60)
    
    # 分析配置
    analyze_config()
    
    # 检查频繁写入
    check_frequent_writes()
    
    print("\n" + "="*60)
    
    # 提供选项
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        monitor = FileChangeMonitor()
        monitor.monitor(interval=2)
    else:
        print("\n💡 使用方法:")
        print("  python diagnose_stability.py          # 快速诊断")
        print("  python diagnose_stability.py --monitor # 持续监控文件变化")
        print("\n运行持续监控以找出导致重载的具体文件")
        print("="*60)
