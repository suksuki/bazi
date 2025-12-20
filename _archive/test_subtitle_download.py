#!/usr/bin/env python3
"""
测试字幕下载功能
检查系统是否能够成功下载CC字幕
"""

from learning.video_downloader import VideoDownloader
from core.config_manager import ConfigManager
import sys

def test_subtitle_download():
    """测试字幕下载"""
    print("=" * 60)
    print("🔍 字幕下载功能测试")
    print("=" * 60)
    
    # 1. 检查配置
    cm = ConfigManager()
    subtitle_priority = cm.get('subtitle_priority', True)
    subtitle_langs = cm.get('subtitle_languages', [])
    
    print(f"\n📋 当前配置:")
    print(f"  • 字幕优先级: {'✅ 开启' if subtitle_priority else '❌ 关闭'}")
    print(f"  • 语言优先级: {', '.join(subtitle_langs)}")
    
    # 2. 测试视频（已知有字幕的视频）
    test_videos = [
        {
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'name': 'Rick Astley - Never Gonna Give You Up (有英文字幕)'
        },
        # 添加你正在测试的视频URL
    ]
    
    if len(sys.argv) > 1:
        # 从命令行参数添加视频
        test_videos.append({
            'url': sys.argv[1],
            'name': '用户提供的视频'
        })
    
    downloader = VideoDownloader()
    
    print(f"\n🎬 开始测试 {len(test_videos)} 个视频:")
    print("-" * 60)
    
    for idx, video in enumerate(test_videos, 1):
        print(f"\n[{idx}/{len(test_videos)}] {video['name']}")
        print(f"  URL: {video['url']}")
        
        try:
            # 测试字幕下载
            sub_path, sub_title = downloader._try_download_subs(video['url'])
            
            if sub_path:
                print(f"  ✅ 字幕下载成功！")
                print(f"     标题: {sub_title}")
                print(f"     路径: {sub_path}")
                
                # 读取前几行字幕内容
                try:
                    with open(sub_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:5]
                        print(f"     预览: {' '.join(lines[:2]).strip()[:100]}...")
                except Exception as e:
                    print(f"     预览失败: {e}")
            else:
                print(f"  ⚠️  未找到字幕")
                print(f"     原因: 视频可能没有提供CC字幕或自动字幕")
                
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    test_subtitle_download()
