import requests
from bs4 import BeautifulSoup
import sys

url = "https://www.youtube.com/@LinZixuan4133"
if len(sys.argv) > 1:
    url = sys.argv[1]

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    r = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Method 1: <title> tag
    print(f"Title Tag: {soup.title.string if soup.title else 'None'}")
    
    # Method 2: Meta tags
    meta_title = soup.find("meta", property="og:title")
    print(f"OG Title: {meta_title['content'] if meta_title else 'None'}")
    
    meta_site = soup.find("meta", property="og:site_name")
    print(f"Site Name: {meta_site['content'] if meta_site else 'None'}")

except Exception as e:
    print(f"Error: {e}")
