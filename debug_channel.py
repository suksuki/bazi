from learning.video_miner import VideoMiner
import sys

url = "https://www.youtube.com/playlist?list=PLzMcBGfZo4-kCLWHEm9V9RL67W6e4t27c" # Example playlist (Tech With Tim)
if len(sys.argv) > 1:
    url = sys.argv[1]

print(f"Testing URL: {url}")
miner = VideoMiner()
ids, err = miner.get_channel_videos(url)

if ids:
    print(f"Success! Found {len(ids)} videos.")
    print(ids[:5])
else:
    print(f"Failed: {err}")
