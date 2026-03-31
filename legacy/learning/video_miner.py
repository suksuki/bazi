from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

class VideoMiner:
    def __init__(self):
        pass

    def get_video_id(self, url):
        """
        Extracts video ID from YouTube URL.
        """
        query = urlparse(url)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return None

    def fetch_transcript(self, url):
        """
        Fetches transcript from YouTube video.
        Returns combined text string or None if failed.
        """
        video_id = self.get_video_id(url)
        if not video_id:
            return None, "Invalid YouTube URL"
        
        try:
            # CORRECT API Usage for this environment:
            # The installed version requires instantiation: api = YouTubeTranscriptApi()
            # Then call api.list(video_id)
            
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            
            # Try to find a manual or generated transcript in Chinese or English
            try:
                # Try Chinese (Simplified/Traditional)
                transcript = transcript_list.find_transcript(['zh-CN', 'zh-Hans', 'zh-TW', 'zh-Hant', 'zh'])
            except:
                try:
                    # Try English
                    transcript = transcript_list.find_transcript(['en'])
                except:
                     # Fallback: just get the first available one (could be auto-generated)
                    transcript = next(iter(transcript_list))
            
            # Fetch the actual content
            data = transcript.fetch()
            
            # Combine text
            # Fix: The data is a list of objects, not dicts in this version
            full_text = " ".join([t.text for t in data])
            return full_text, "Success"
            
        except Exception as e:
            msg = str(e)
            if "TranscriptsDisabled" in msg or "Subtitles are disabled" in msg or "NoTranscriptFound" in msg:
                # Fallback to Whisper ASR - Return a special flag to let main_app handle the progress UI
                return None, "WHISPER_FALLBACK"
            
            return None, f"读取失败: {msg}"

    def download_audio(self, url):
        """
        Step 1: Download audio via yt-dlp. Returns (file_path, error_msg)
        """
        import yt_dlp
        import os
        
        video_id = self.get_video_id(url)
        # Use a consistent filename based on ID
        output_template = f"audio_{video_id}"
        expected_file = f"{output_template}.mp3"
        
        # Cleanup previous run if exists
        if os.path.exists(expected_file):
            try:
                os.remove(expected_file)
            except:
                pass
        
        # 1. Download Audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_template, # yt-dlp adds extension
            'quiet': True,
            'overwrites': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # yt-dlp might output .mp3 directly depending on FFmpeg availability
            # verifying file existence
            if not os.path.exists(expected_file):
                # Try finding any file starting with output_template
                for f in os.listdir('.'):
                    if f.startswith(output_template):
                        expected_file = f
                        break
            
            if not os.path.exists(expected_file):
                 return None, "Download failed (Audio file not found)"
                 
            return expected_file, None
            
        except Exception as e:
            return None, f"Download failed: {e}"

    def transcribe_file(self, file_path):
        """
        Step 2: Transcribe local audio file with Whisper. Returns (text, error_msg)
        """
        import whisper
        import os
        
        try:
            # 2. Transcribe
            # Load model (this will cache it in ~/.cache/whisper)
            # Using 'base' model for balance of speed/accuracy.
            model = whisper.load_model("base")
            result = model.transcribe(file_path, fp16=False)
            
            # 3. Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return result["text"], None
            
        except Exception as e:
            return None, f"Whisper 听写失败: {e}"

    def get_channel_videos(self, channel_url):
        """
        Fetch all video IDs from a YouTube channel/playlist using yt-dlp.
        Returns (video_ids_list, error_msg)
        """
        import yt_dlp
        
        ydl_opts = {
            'extract_flat': True,  # Don't download, just extract metadata
            'quiet': True,
            'ignoreerrors': True, # Skip private/deleted videos without crashing
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(channel_url, download=False)
                
            if 'entries' in result:
                # Playlist or Channel results
                video_ids = [entry['id'] for entry in result['entries'] if entry and 'id' in entry]
                return video_ids, None
            else:
                 return None, "No videos found (Check URL)"
        except Exception as e:
            return None, f"Channel Fetch Error: {e}"

    def cleanup_temp_files(self):
        """
        Removes any leftover temporary files (audio_*.mp3, *.webm, etc)
        """
        import os
        import glob
        
        count = 0
        patterns = ["audio_*", "*.mp4", "*.mkv", "*.webm", "*.part"]
        
        for p in patterns:
            for f in glob.glob(p):
                try:
                    os.remove(f)
                    count += 1
                except:
                    pass
        return count

    def get_history(self):
        """
        Returns a set of processed video IDs.
        """
        import os
        history_path = os.path.join(os.path.dirname(__file__), "../data/video_history.txt")
        if not os.path.exists(history_path):
            return set()
        
        with open(history_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def mark_processed(self, video_id):
        """
        Marks a video ID as processed in the history file.
        """
        import os
        history_path = os.path.join(os.path.dirname(__file__), "../data/video_history.txt")
        with open(history_path, 'a', encoding='utf-8') as f:
            f.write(f"{video_id}\n")

if __name__ == "__main__":
    # Test
    miner = VideoMiner()
    # url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Rick Roll usually has captions
    # print(miner.fetch_transcript(url))
