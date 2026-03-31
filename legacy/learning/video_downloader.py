
import yt_dlp
import os

class VideoDownloader:
    """
    Handles downloading audio from YouTube, TikTok, X (Twitter), etc.
    using yt-dlp.
    """
    def __init__(self, download_dir="data/media_cache"):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    def get_channel_info(self, url):
        """
        Returns (videos_list, channel_title).
        Recursively scans tabs (Videos, Live, Shorts) to find all content.
        """
        ydl_opts = {
            'extract_flat': True, 
            'quiet': True,
            'ignoreerrors': True,
        }
        videos = []
        channel_title = None
        extract_error = None
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                res = ydl.extract_info(url, download=False)
                
                channel_title = res.get('channel') or res.get('uploader') or res.get('title')
                
                # We will collect all potential video entries here
                all_entries = []
                scanned_urls = set()
                scanned_urls.add(url)
                
                # Initial entries from the main URL
                if 'entries' in res:
                    all_entries.extend(list(res['entries']))
                
                # Queue of potential Tabs/Sub-channels to scan
                tabs_to_scan = []
                
                # 1. Identify Tabs in the initial list
                # We look at the first batch of entries. 
                # If they look like Tabs (long IDs or specific titles), we add them to scan queue.
                for e in list(all_entries):
                    if not e: continue
                    e_id = e.get('id', '')
                    e_url = e.get('url', '')
                    e_title = e.get('title', '')
                    
                    is_tab = False
                    
                    # ID check: Channel/Playlist IDs are usually 24 chars starting with UC or PL
                    if e_id and (e_id.startswith('UC') or len(e_id) > 18):
                        is_tab = True
                        
                    # Title/URL heuristic
                    if '/videos' in e_url or '/shorts' in e_url or '/streams' in e_url or '/live' in e_url:
                        is_tab = True
                    if e_title.endswith(' - Videos') or e_title.endswith(' - Live') or e_title.endswith(' - Shorts'):
                        is_tab = True
                        
                    if is_tab:
                        t_url = e_url or e.get('original_url')
                        # Sanitize URL if needed
                        if t_url and 'http' not in t_url:
                             # Try to construct? Usually extact_flat gives full url or relative
                             if t_url.startswith('/'): t_url = f"https://www.youtube.com{t_url}"
                        
                        if t_url and t_url not in scanned_urls:
                             tabs_to_scan.append(t_url)
                             scanned_urls.add(t_url)

                # 2. Scan the Tabs
                for t_url in tabs_to_scan:
                    try:
                        tab_res = ydl.extract_info(t_url, download=False)
                        if 'entries' in tab_res:
                            all_entries.extend(list(tab_res['entries']))
                    except:
                        pass
                        
                # 3. Filter and Deduplicate to get final Videos
                seen_ids = set()
                real_videos = []
                
                for entry in all_entries:
                    if not entry: continue
                    
                    v_id = entry.get('id')
                    v_title = entry.get('title', '')
                    if not v_title: v_title = 'Unknown'
                    
                    if not v_id: continue
                    if v_id in seen_ids: continue
                    
                    v_url = entry.get('url') or entry.get('original_url')
                    if not v_url: v_url = f"https://www.youtube.com/watch?v={v_id}"
                    
                    # Check for Real Video (short ID)
                    if not v_id.startswith('UC') and len(v_id) <= 15 and 'watch?v=' in v_url:
                        if entry.get('ie_key') != 'YoutubeTab':
                            seen_ids.add(v_id)
                            
                            # Try to detect CC (Note: varying availability in flat extraction)
                            cc_tag = ""
                            if entry.get('subtitles') or entry.get('automatic_captions') or entry.get('is_live'):
                                cc_tag = " 💬"
                                
                            real_videos.append({
                                'url': v_url, 
                                'title': v_title + cc_tag, 
                                'id': v_id
                            })
                
                # HEURISTIC: If main scan yielded 0 videos, explicitly try '/videos' and '/streams'
                # This fixes channels where Tabs are not exposed in metadata (User verified fix)
                if not real_videos:
                    explicit_suffixes = ['/videos', '/streams']
                    for suffix in explicit_suffixes:
                        if url.endswith(suffix): continue
                        target_url = url.rstrip('/') + suffix
                        try:
                            s_res = ydl.extract_info(target_url, download=False)
                            if 'entries' in s_res:
                                for entry in s_res['entries']:
                                    if not entry: continue
                                    v_id = entry.get('id')
                                    # Strict filter again
                                    if v_id and not v_id.startswith('UC') and len(v_id) <= 15:
                                         v_url = entry.get('url') or entry.get('original_url')
                                         if not v_url: v_url = f"https://www.youtube.com/watch?v={v_id}"
                                         
                                         if 'watch?v=' in v_url and v_id not in seen_ids:
                                              seen_ids.add(v_id)
                                              real_videos.append({
                                                  'url': v_url, 
                                                  'title': entry.get('title', 'Unknown'), 
                                                  'id': v_id
                                              })
                        except: pass

                if real_videos:
                    videos = real_videos
                else:
                    # Fallback: Return the Tabs/Sub-channels themselves if no videos found
                    # This allows the user to see/click the "Videos", "Live" tabs manually
                    seen_ids = set() # Reset
                    for entry in all_entries:
                         v_id = entry.get('id')
                         v_title = entry.get('title', '')
                         v_url = entry.get('url') or entry.get('original_url')
                         
                         if v_id and (v_id.startswith('UC') or len(v_id) > 15) and v_url:
                             if v_id not in seen_ids:
                                 seen_ids.add(v_id)
                                 # Clean title
                                 display_title = v_title.replace(" - YouTube", "")
                                 videos.append({'url': v_url, 'title': f"📂 {display_title}", 'id': v_id})

                        
        except Exception as e:
            extract_error = str(e)
            
        # Fallback for Title (HTML Scraping) if yt-dlp missed it or failed
        if not channel_title or channel_title == "Unknown Channel":
            try:
                import requests
                from bs4 import BeautifulSoup
                # Simple scraper
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0"}
                r = requests.get(url, headers=headers, timeout=3)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    meta_title = soup.find("meta", property="og:title")
                    if meta_title: 
                        channel_title = meta_title['content']
                    elif soup.title:
                        channel_title = soup.title.string.replace(" - YouTube", "")
            except:
                pass
        
        # If we failed to get videos AND failed to get title, return error
        if not videos and not channel_title and extract_error:
            return [], f"Error: {extract_error}"
            
        # If we have title but no videos (maybe network block on API but HTML worked), return title
        return videos, channel_title

    def download_audio(self, url, fetch_subs=True):
        """
        Downloads audio or extracts subtitles if available.
        Returns (file_path, title, duration, is_subtitle).
        """
        # 1. Try to get Subtitles first (Fastest)
        if fetch_subs:
            sub_path, sub_title = self._try_download_subs(url)
            if sub_path:
                 return sub_path, sub_title, 0, True

        # 2. Fallback to Audio Download
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.download_dir}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info['id']
                title = info.get('title', video_id)
                duration = info.get('duration', 0)
                
                # Filename is predictable based on template + codec
                file_path = os.path.join(self.download_dir, f"{video_id}.mp3")
                return file_path, title, duration, False
        except Exception as e:
            print(f"Download Error {url}: {e}")
            return None, None, 0, False

    def _try_download_subs(self, url):
        """
        Attempts to download auto-generated or manual subtitles.
        Returns (path, title) or (None, None).
        """
        # 从配置中读取字幕语言优先级
        from core.config_manager import ConfigManager
        cm = ConfigManager()
        subtitle_langs = cm.get('subtitle_languages', ['zh-Hans', 'zh-Hant', 'zh-CN', 'zh-TW', 'zh', 'en'])
        
        ydl_opts = {
            'skip_download': True,
            'writeautomaticsub': True,
            'writesubtitles': True,
            'subtitleslangs': subtitle_langs,  # 使用配置中的语言优先级
            'outtmpl': f'{self.download_dir}/%(id)s', # suffix added by yt-dlp
            'quiet': True,
        }
        try:
             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                v_id = info['id']
                v_title = info.get('title', 'Unknown Title')
                
                # Check for files
                # yt-dlp saves as [id].zh-Hans.vtt or similar
                # We need to find the file
                for f in os.listdir(self.download_dir):
                    if f.startswith(v_id) and f.endswith('.vtt'):
                        # Convert VTT to Text
                        vtt_path = os.path.join(self.download_dir, f)
                        txt_path = vtt_path + ".txt"
                        self._vtt_to_txt(vtt_path, txt_path)
                        # clean vtt
                        os.remove(vtt_path)
                        
                        # 提取语言信息用于日志
                        lang = f.replace(v_id, '').replace('.vtt', '').strip('.')
                        print(f"✅ 成功下载字幕 [{lang}]: {v_title}")
                        return txt_path, v_title
        except Exception as e:
            print(f"Sub Download Error: {e}")
        return None, None

    def _vtt_to_txt(self, vtt_path, txt_path):
        # Simple VTT cleaner
        unique_lines = set()
        with open(vtt_path, 'r', errors='ignore') as fin, open(txt_path, 'w') as fout:
            for line in fin:
                line = line.strip()
                if '-->' in line or not line or line == 'WEBVTT': continue
                # Remove timestamps/tags if strictly needed (some lines are just IDs)
                if line not in unique_lines:
                    fout.write(line + "\n")
                    unique_lines.add(line)
    
    def cleanup(self, file_path):
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")
            except: pass
