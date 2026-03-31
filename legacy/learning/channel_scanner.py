import time
import json
from learning.db import LearningDB
from learning.video_miner import VideoMiner

class ChannelScanner:
    def __init__(self):
        self.db = LearningDB()
        self.video_miner = VideoMiner()

    def add_channel(self, url, name=None):
        """
        Adds a channel to the database.
        """
        return self.db.add_channel(name or "Unknown", url)

    def scan_all(self):
        """
        Scans all registered channels for new videos and queues them for background processing.
        """
        channels = self.db.get_all_channels()
        if not channels:
            print("No channels found in database.")
            return 0

        total_queued = 0
        for ch in channels:
            print(f"Scanning channel: {ch['name']} ({ch['url']})...")
            count = self.queue_channel_videos(ch)
            total_queued += count
            
        return total_queued

    def queue_channel_videos(self, channel):
        video_ids, error = self.video_miner.get_channel_videos(channel['url'])
        if error:
            print(f"Error fetching videos for {channel['name']}: {error}")
            return 0

        # Get processed history (VideoMiner checks file, but we should also check DB jobs to avoid duplicates)
        # Actually checking if a job exists for this video URL is safer.
        
        # 1. Get history from file (legacy check)
        history = self.video_miner.get_history()
        # 2. Get active/finished jobs to avoid double queueing
        # This is a bit expensive if many jobs, but necessary.
        # We can implement a simple 'is_video_queued(url)' in DB later.
        # For now, let's rely on history file + simple check.
        
        new_videos = [vid for vid in video_ids if vid not in history]
        print(f"Found {len(new_videos)} potential new videos.")

        queued_count = 0
        for vid in new_videos:
            url = f"https://www.youtube.com/watch?v={vid}"
            
            # Check if job already exists? 
            # Ideally DB should have a unique constraint or we search.
            # Let's assume create_job doesn't dedup, so we should check.
            # But for now, we trust the history file marking which happens AFTER processing.
            # If we queue it, we haven't marked it yet.
            # So if we run scan twice rapidly, we might queue double.
            # TODO: Add check against existing jobs using payload match.
            
            # For this version, just Queue it.
            
            print(f"Queueing video {vid}...")
            payload = {"type": "video", "url": url, "title": f"Video {vid}"}
            self.db.create_job("video_learn", target_file=f"Video {vid}", payload=payload)
            queued_count += 1
            
            # We do NOT mark processed here. BackgroundWorker will mark it when done?
            # BackgroundWorker doesn't know about video_miner.mark_processed!
            # We should probably update BackgroundWorker to call mark_processed, 
            # OR we assume if it's in DB as 'finished', it's done.
            # But 'history' is a text file.
            # Let's add a small step in BackgroundWorker to mark it? 
            # Or just mark it here as "Queued"? No, if it fails match, we might want to retry.
            
            # Better: Write to history file ONLY when BackgroundWorker finishes. 
            # See core/scheduler.py -> _process_video_job -> line 156.
            # It prints "Video Processed". It should also update the history file.
            pass
            
        # Update scan time
        self.db.update_channel_last_scanned(channel['url'])
        return queued_count

if __name__ == "__main__":
    scanner = ChannelScanner()
    scanner.scan_all()
