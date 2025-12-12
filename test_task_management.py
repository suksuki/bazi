#!/usr/bin/env python3
"""
测试任务管理新功能
Test script for new task management features
"""

import sys
sys.path.insert(0, '/home/jin/bazi_predict')

from learning.db import LearningDB
import json

def test_batch_operations():
    """测试批量操作功能"""
    print("=" * 50)
    print("测试任务管理批量操作功能")
    print("=" * 50)
    
    db = LearningDB()
    
    # 1. 测试创建多个测试任务
    print("\n1️⃣ 创建测试任务...")
    test_jobs = []
    for i in range(5):
        payload = {
            "type": "test",
            "title": f"测试任务 {i+1}",
            "description": "这是一个测试任务"
        }
        job_id = db.create_job(
            "test_job",
            f"test_file_{i+1}.txt",
            payload=payload
        )
        test_jobs.append(job_id)
        print(f"   ✓ 创建任务 ID: {job_id}")
    
    # 2. 测试获取任务
    print("\n2️⃣ 获取所有待处理任务...")
    pending_jobs = db.get_jobs_by_status(['pending'], limit=100)
    print(f"   ✓ 找到 {len(pending_jobs)} 个待处理任务")
    
    # 3. 测试批量更新状态
    print("\n3️⃣ 测试批量暂停...")
    count = db.batch_update_status(test_jobs, 'paused')
    print(f"   ✓ 已暂停 {count} 个任务")
    
    # 验证
    paused_jobs = db.get_jobs_by_status(['paused'])
    paused_ids = [j['id'] for j in paused_jobs if j['id'] in test_jobs]
    print(f"   ✓ 验证：{len(paused_ids)} 个任务处于暂停状态")
    
    # 4. 测试批量恢复
    print("\n4️⃣ 测试批量恢复...")
    count = db.batch_update_status(test_jobs, 'pending')
    print(f"   ✓ 已恢复 {count} 个任务")
    
    # 5. 测试批量删除
    print("\n5️⃣ 测试批量删除...")
    count = db.batch_delete_jobs(test_jobs)
    print(f"   ✓ 已删除 {count} 个任务")
    
    # 验证
    deleted_jobs = db.get_jobs_by_status(['deleted'])
    deleted_ids = [j['id'] for j in deleted_jobs if j['id'] in test_jobs]
    print(f"   ✓ 验证：{len(deleted_ids)} 个任务已标记为删除")
    
    # 6. 测试获取任务计数
    print("\n6️⃣ 测试任务统计...")
    counts = db.get_job_counts()
    print("   当前任务统计:")
    for status, count in counts.items():
        status_names = {
            'running': '🟢 运行中',
            'pending': '🔵 等待中',
            'paused': '🟡 已暂停',
            'failed': '🔴 失败',
            'finished': '✅ 已完成',
            'deleted': '🗑️ 已删除'
        }
        emoji = status_names.get(status, status)
        print(f"   {emoji}: {count}")
    
    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")
    print("=" * 50)

def show_current_jobs():
    """显示当前所有任务"""
    print("\n📋 当前所有任务（不含已删除）:")
    print("-" * 50)
    
    db = LearningDB()
    jobs = db.get_all_jobs(include_deleted=False)
    
    if not jobs:
        print("   暂无任务")
    else:
        for job in jobs[:10]:  # 只显示前10个
            try:
                payload = json.loads(job['payload']) if job['payload'] else {}
                title = payload.get('title', job['target_file'])
            except:
                title = job['target_file']
            
            status_icons = {
                'running': '🟢',
                'pending': '🔵',
                'paused': '🟡',
                'failed': '🔴',
                'finished': '✅'
            }
            icon = status_icons.get(job['status'], '⚪')
            
            print(f"   {icon} [{job['id']}] {title}")
            print(f"      状态: {job['status']} | 进度: {job['current_progress']}/{job['total_work']}")
        
        if len(jobs) > 10:
            print(f"\n   ... 还有 {len(jobs) - 10} 个任务")
    
    print("-" * 50)

if __name__ == "__main__":
    try:
        # 先显示当前任务
        show_current_jobs()
        
        # 运行测试
        test_batch_operations()
        
        # 再次显示任务（应该多了几个测试任务）
        show_current_jobs()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
