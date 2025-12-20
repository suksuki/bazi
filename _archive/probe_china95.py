
import requests
from bs4 import BeautifulSoup

url = "http://bbs.china95.net/forum-103-1.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'http://bbs.china95.net/'
}

try:
    print(f"Connecting to {url}...")
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Encoding (Auto): {resp.encoding}")
    print(f"Apparent Encoding: {resp.apparent_encoding}")
    
    # Force correct decoding
    resp.encoding = 'gbk' 
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Try finding threads
    threads = []
    for a in soup.find_all('a'):
        href = a.get('href')
        if href and 'thread-' in href:
            threads.append(href)
            
    print(f"Found {len(threads)} thread links.")
    if threads:
        print(f"Sample: {threads[:3]}")
    else:
        print("SAMPLE HTML (First 500 chars):")
        print(resp.text[:500])

except Exception as e:
    print(f"Error: {e}")
