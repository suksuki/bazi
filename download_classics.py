import requests
from bs4 import BeautifulSoup
import os
import time

def download_book(book_name):
    # Search on Gushiwen (Ancient Texts)
    print(f"📚 Searching gushiwen.cn for {book_name}...")
    search_url = f"https://so.gushiwen.cn/search.aspx?type=guwen&value={book_name}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find the first book link
        # Structure often: <div class="sons"><div class="cont"><p><a href="..."><b>Title</b></a></p>...
        book_link = None
        
        # Heuristic search for result
        for a in soup.find_all('a'):
            if book_name in a.get_text():
                href = a.get('href')
                if "guwen/book_" in href:
                    book_link = href if href.startswith('http') else f"https://so.gushiwen.cn{href}"
                    print(f"🔗 Found Book: {book_link}")
                    break
        
        if not book_link:
            print("❌ Book not found on Gushiwen.")
            return

        # Scrape Chapters
        resp = requests.get(book_link, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        chapters = []
        # Main Logic: <div class="bookcont"> ... <span><a href="...">Chapter 1</a></span> ...
        bookcont = soup.find('div', class_='bookcont')
        if bookcont:
            for a in bookcont.find_all('a'):
                title = a.get_text().strip()
                href = a.get('href')
                full_link = href if href.startswith('http') else f"https://so.gushiwen.cn{href}"
                chapters.append((title, full_link))
                
        print(f"📖 Found {len(chapters)} chapters.")
        
        full_text = f"# {book_name}\n\nSource: {book_link}\n\n"
        
        for idx, (title, link) in enumerate(chapters):
            print(f"  Downloading [{idx+1}/{len(chapters)}]: {title}...")
            try:
                c_resp = requests.get(link, headers=headers, timeout=10)
                c_soup = BeautifulSoup(c_resp.text, 'html.parser')
                
                # Content is usually in <div class="contson">
                contson = c_soup.find('div', class_='contson')
                if contson:
                    text = contson.get_text(separator='\n').strip()
                    full_text += f"\n\n## {title}\n\n{text}"
                else:
                    print(f"    ⚠️ No content found for {title}")
                
                time.sleep(0.3)
            except Exception as e:
                print(f"    Failed: {e}")
                
        # Save
        save_dir = "data/books"
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, f"{book_name}.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"✅ Saved {len(full_text)} chars to {path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    download_book("三命通会")
    download_book("渊海子平")
