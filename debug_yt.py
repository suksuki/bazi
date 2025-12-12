import yt_dlp
import json
import sys

# Default URL or from args
url = "https://www.youtube.com/@LinZixuan4133"
if len(sys.argv) > 1:
    url = sys.argv[1]

print(f"Testing URL: {url}")

ydl_opts = {
    'extract_flat': True,
    'quiet': True,
    'ignoreerrors': True,
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(url, download=False)
        print("--- Result Keys ---")
        print(list(res.keys()))
        
        print("\n--- Metadata Candidates ---")
        print(f"Title: {res.get('title')}")
        print(f"Channel: {res.get('channel')}")
        print(f"Uploader: {res.get('uploader')}")
        print(f"ID: {res.get('id')}")
        
        if 'entries' in res:
            entry_count = len(list(res['entries']))
            print(f"\nEntries Count: {entry_count}")
            # Check first entry
            # entries is a generator if not listed? extract_info returns dict with entries iterator usually?
            # actually extract_flat returns dict.
            pass
            
except Exception as e:
    print(f"Error: {e}")
