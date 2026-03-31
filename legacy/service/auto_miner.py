#!/usr/bin/env python3
"""
Auto Miner Module (The Harvester)
Project Crimson Vein - Autonomous Acquistion Layer

Implements the 3-Method Automatic Mining Strategy:
1. Search Engine Automation (DuckDuckGo HTML)
2. Site Traversal (Heuristic Listing Detection)
3. Exploratory Discovery (Link Following)
"""

import requests
import re
import time
import random
import urllib.parse
from typing import List, Set

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from service.web_hunter import WebHunter
from service.processor import ContentProcessor

class AutoMiner:
    # 用户指定的固定关键词策略
    SEARCH_KEYWORDS = [
        "八字 案例 分析",
        "八字 实战 命例",
        "八字 真实 反馈",
        "命理 案例 应验",
        "actual bazi case study", # 补充英文源
        "bazi analysis famous people"
    ]
    
    # Fallback Seed URLs (Used when Search fails/timeout)
    SEED_URLS = [
        "https://www.nanxuzi.com/sm/bzal/",
        "http://bbs.china95.net/forum-103-1.html",
        "http://www.wuzao.com/bazijichu/"
    ]
    
    
    def __init__(self):
        self.hunter = WebHunter()
        self.processor = ContentProcessor()
        self.visited_urls: Set[str] = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Load VIP List from File
        self.target_vips = []
        self._load_vip_list()

    def _load_vip_list(self):
        """Loads celebrities from data/dictionaries/celebrities.txt"""
        import os
        dict_path = os.path.join(os.path.dirname(__file__), "../data/dictionaries/celebrities.txt")
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.target_vips.append(line)
            print(f"📖 [AutoMiner] Loaded {len(self.target_vips)} VIP targets from dictionary.")
        else:
            print("⚠️ [AutoMiner] Dictionary not found. Using fallback list.")
            self.target_vips = ["马云", "Elon Musk", "特朗普"] # Minimal fallback

    def start_autopilot(self, max_cycles=5, mode="mixed"):
        """
        Main Loop for the Automation.
        Modes:
        - "mixed": The original round-robin strategy.
        - "celebrity_only": Focus exclusively on the VIP dictionary (Baike + Bazi).
        """
        print(f"🚀 [AutoMiner] Engaging Autopilot. Mode: {mode}")
        
        cycle = 0
        while cycle < max_cycles:
            # Determine Phase
            if mode == "celebrity_only":
                phase = 0 # Force Celebrity Phase
            else:
                phase = cycle % 4
            
            if phase == 0:
                # Method 4: Celebrity Hunter (NEW & BEST STRATEGY)
                if self.target_vips:
                    target = random.choice(self.target_vips)
                    print(f"\n🏆 [Cycle {cycle+1}/{max_cycles}] Executing Method 4: Celebrity Hunter Target: [{target}]")
                    self._mine_celebrity_spec(target)
                else:
                    print("   ⚠️ No VIP targets loaded.")

            elif phase == 1:
                # Method 3: Local Archive Scan
                print(f"\n📂 [Cycle {cycle+1}/{max_cycles}] Executing Method 3: Mining Local Video Archives")
                self._mine_local_archives(limit=5)
            
            elif phase == 2:
                # Method 2: China95
                print(f"\n🏯 [Cycle {cycle+1}/{max_cycles}] Executing Method 2: Deep Dive into YuanHeng (China95)")
                self._mine_china95_forum(limit=3)
                
            else: # phase == 3
                # Method 1: General Search
                keyword = random.choice(self.SEARCH_KEYWORDS)
                print(f"\n📡 [Cycle {cycle+1}/{max_cycles}] Executing Method 1: Search for '{keyword}'")
                
                urls = self._search_baidu(keyword, limit=3)
                if not urls:
                     urls = [random.choice(self.SEED_URLS)]
                
                for url in urls:
                    if url in self.visited_urls: continue
                    self.visited_urls.add(url)
                    self.hunter.hunt_from_url(url)
                    time.sleep(2)
            

            cycle += 1
            print(f"💤 Cycle complete. Cooling down for 3s...")
            time.sleep(3)

    def _mine_celebrity_spec(self, name):
        """
        Specific strategy: Hunt for a specific person's chart + bio.
        Prioritizes Encyclopedia sources for Ground Truth.
        """
        print(f"   🎯 [Celebrity Hunter] Targeting: {name}")
        
        # 1. Primary Target: Baidu Baike (Standard Bio)
        # We explicitly search for the Baike entry
        url_baike = f"https://baike.baidu.com/item/{urllib.parse.quote(name)}"
        # But we can't just guess URL, better to search "Name 百度百科"
        
        sys_urls = []
        
        # Search 1: Baidu Baike
        print(f"     📖 Searching {name} 百度百科 (via Google)...")
        urls_1 = self._search_google(f"{name} 百度百科", limit=1)
        sys_urls.extend(urls_1)
        
        # Search 2: Wikipedia (Accessible in Korea!)
        print(f"     📖 Searching {name} 维基百科 (via Google)...")
        urls_2 = self._search_google(f"{name} 维基百科", limit=1)
        sys_urls.extend(urls_2)
        
        # Search 3: Bazi Chart (Necessary for CaseDB, otherwise we only have story)
        # We need at least one source for the birth time/chart
        print(f"     🔮 Searching {name} 八字排盘 (via Google)...")
        urls_3 = self._search_google(f"{name} 八字", limit=1)
        sys_urls.extend(urls_3)
        
        print(f"   ✅ Found {len(sys_urls)} sources. Starting extraction...")
        
        for url in sys_urls:
            if url in self.visited_urls: continue
            self.visited_urls.add(url)
            self.hunter.hunt_from_url(url)
            time.sleep(1)

    def _mine_local_archives(self, limit=5):
        """
        Method 3 Implementation: Scan local video transcripts (data/media_cache)
        """
        import os
        import glob
        
        # Path relative to service/auto_miner.py -> ../data/media_cache
        base_dir = os.path.join(os.path.dirname(__file__), "../data/media_cache")
        patterns = ["*.vtt", "*.txt"]
        all_files = []
        for p in patterns:
            all_files.extend(glob.glob(os.path.join(base_dir, p)))
            
        # Shuffle to get random samples each time
        random.shuffle(all_files)
        
        count = 0
        print(f"   📂 Found {len(all_files)} local transcripts. Processing random {limit}...")
        
        for f_path in all_files:
            if count >= limit: break
            
            # Use pseudo-URL for tracking
            file_name = os.path.basename(f_path)
            pseudo_url = f"file://{file_name}"
            
            if pseudo_url in self.visited_urls: continue
            self.visited_urls.add(pseudo_url)
            
            print(f"     📜 Reading Local File: {file_name}")
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Special cleaner for VTT to get pure text
                if f_path.endswith('.vtt'):
                    content = self._clean_vtt(content)
                
                # Send to Processor
                # We mock a web result structure
                mock_text = f"Title: {file_name}\n\n{content}"
                self.processor.process_text(mock_text, pseudo_url)
                count += 1
                
            except Exception as e:
                print(f"   ❌ Read Error {file_name}: {e}")

    def _clean_vtt(self, vtt_content):
        """
        Simple cleaner to strip timestamps from WebVTT
        """
        lines = []
        for line in vtt_content.splitlines():
            line = line.strip()
            # Skip header, arrows, empty lines
            if not line: continue
            if "WEBVTT" in line: continue
            if "-->" in line: continue
            if line[0].isdigit() and line.endswith('%'): continue # occasional percentage
            lines.append(line)
        return " ".join(lines)

    def _search_baidu(self, query: str, limit=10) -> List[str]:
        """
        Method 1 Implementation: Scrape Baidu (Better for Chinese Content)
        """
        base_url = "https://www.baidu.com/s"
        data = {'wd': query}
        
        try:
            resp = requests.get(base_url, params=data, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                raise Exception(f"Status {resp.status_code}")
            
            # Simple Regex Extraction for Baidu links (bs4 selector can be brittle on Baidu)
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            # Baidu organic results are usually in div.result or div.c-container
            for div in soup.find_all('div', class_='c-container'):
                h3 = div.find('h3')
                if h3:
                    a = h3.find('a')
                    if a and a.get('href'):
                        link = a['href']
                        # Baidu uses intermediate redirect links. We can follow them or use distinct check.
                        # For simple mining, we just add the redirect link, WebHunter will resolve it.
                        results.append(link)
                        if len(results) >= limit: break
            
            return results
        except Exception as e:
            print(f"   ❌ Baidu Search failed: {e}")
            print("   ⚠️ Engaging Fallback Strategy: Using Seed URLs")
            return [random.choice(self.SEED_URLS)]

    def _mine_china95_forum(self, limit=5):
        """
        Specialized Strategy for YuanHengLiZhen (china95.net)
        Target: 八字实例反馈版 (fid=103)
        """
        home_url = "http://bbs.china95.net/"
        board_url = "http://bbs.china95.net/forum-103-1.html" 
        base_domain = "http://bbs.china95.net/"
        
        try:
            session = requests.Session()
            session.headers.update(self.headers)
            
            # 1. Warm-up: Visit Home to get Cookies
            # print(f"   🏯 Accessing Home for Cookie jar...")
            try:
                session.get(home_url, timeout=10)
            except:
                pass # Proceed anyway
                
            print(f"   🏯 Accessing Board: {board_url}")
            resp = session.get(board_url, timeout=15)
            
            # Auto-detect encoding
            if resp.encoding == 'ISO-8859-1':
                resp.encoding = resp.apparent_encoding
            
            if "提示信息" in resp.text:
                print("   ⚠️ Forum returned 'Notice' (Anti-Bot Redirect). Waiting 3s...")
                time.sleep(3)
                # Sometimes just refetching works if it was a cookie set interstitial
                resp = session.get(board_url, timeout=15)
                if resp.encoding == 'ISO-8859-1': resp.encoding = resp.apparent_encoding

            if resp.status_code != 200:
                print(f"   ❌ Board access failed: {resp.status_code}")
                return

            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find threads
            threads = []
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and 'thread-' in href and '.html' in href:
                    full_link = urllib.parse.urljoin(base_domain, href)
                    if full_link not in self.visited_urls:
                        threads.append(full_link)
                        # We only want unique thread IDs, deduplicate by ID if needed
                        if len(threads) >= limit: break
            
            if not threads:
                # Fallback: Maybe 'mod=viewthread&tid=...' format?
                for a in soup.find_all('a'):
                     href = a.get('href')
                     if href and 'viewthread' in href:
                         full_link = urllib.parse.urljoin(base_domain, href)
                         if full_link not in self.visited_urls:
                             threads.append(full_link)
                             if len(threads) >= limit: break

            print(f"   🏯 Found {len(threads)} fresh threads. Mining content...")
            
            for t_url in threads:
                if t_url in self.visited_urls: continue
                self.visited_urls.add(t_url)
                print(f"     📜 Mining Thread: {t_url}")
                
                # Use WebHunter to process this URL using the detailed parsing logic
                self.hunter.hunt_from_url(t_url)
                
                time.sleep(random.uniform(2, 5))
                
        except Exception as e:
            print(f"   ❌ China95 Mining Error: {e}")

    def _search_duckduckgo(self, query: str, limit=10) -> List[str]:
        """
        Method 1 Implementation: Scrape DuckDuckGo HTML version (No API key needed)
        """
        base_url = "https://html.duckduckgo.com/html/"
        data = {'q': query}
        
        try:
            resp = requests.post(base_url, data=data, headers=self.headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            # DDG HTML results are in 'a.result__a'
            for link in soup.find_all('a', class_='result__a'):
                href = link.get('href')
                if href:
                    results.append(href)
                    if len(results) >= limit: break
            
            if not results:
                return self._search_bing(query, limit)
            return results
            
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
            return self._search_bing(query, limit)

    def _search_google(self, query: str, limit=10) -> List[str]:
        """
        Method 1 Primary: Scrape Google (Best Quality, High Risk of 429)
        Fallback -> DuckDuckGo
        """
        print(f"     🔍 Google Search: {query}")
        base_url = "https://www.google.com/search"
        params = {'q': query, 'num': limit + 2}
        
        try:
            resp = requests.get(base_url, params=params, headers=self.headers, timeout=10)
            
            if resp.status_code == 429:
                print("     ⚠️ Google Rate Limited (429). Switching to DuckDuckGo...")
                return self._search_duckduckgo(query, limit)
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            # Robust Google Parsing: Find h3, then get parent 'a'
            for h3 in soup.find_all('h3'):
                a = h3.find_parent('a')
                if a and a.get('href'):
                    link = a['href']
                    if link.startswith('http') and 'google.com' not in link:
                        results.append(link)
                        if len(results) >= limit: break
            
            if not results:
                 return self._search_duckduckgo(query, limit)
                 
            return results
            
        except Exception as e:
            print(f"     ❌ Google Failed: {e}")
            return self._search_duckduckgo(query, limit)

    def _search_bing(self, query: str, limit=10) -> List[str]:
        """
        Method 1 Backup: Scrape Bing (Works well internationally)
        """
        print(f"   ⚠️ DDG failed/empty. Falling back to Bing for: {query}")
        base_url = "https://www.bing.com/search"
        data = {'q': query}
        # Bing requires a standard User-Agent
        
        try:
            resp = requests.get(base_url, params=data, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            # Bing results: <li class="b_algo"> <h2> <a href="...">
            import base64
            import urllib.parse
            
            for li in soup.find_all('li', class_='b_algo'):
                h2 = li.find('h2')
                if h2:
                    a = h2.find('a')
                    if a and a.get('href'):
                        link = a['href']
                        
                        # Handle Bing Redirects (bing.com/ck/a?...)
                        if "bing.com/ck/a" in link:
                            try:
                                parsed = urllib.parse.urlparse(link)
                                qs = urllib.parse.parse_qs(parsed.query)
                                if 'u' in qs:
                                    # Bing u parameter is often "a1" + Base64(Target)
                                    # But sometimes it uses a custom encoding. 
                                    # Let's try simple Base64 padding fix if it looks like b64
                                    u_val = qs['u'][0]
                                    # Common trick: Bing adds "a1" prefix on base64? 
                                    # Let's try to remove leading 'a1' if present, as seen in log
                                    if u_val.startswith("a1"):
                                        u_val = u_val[2:]
                                    
                                    # Add padding 
                                    missing_padding = len(u_val) % 4
                                    if missing_padding:
                                        u_val += '=' * (4 - missing_padding)
                                        
                                    decoded_bytes = base64.urlsafe_b64decode(u_val)
                                    real_url = decoded_bytes.decode('utf-8')
                                    link = real_url
                                    print(f"     🔓 Decoded Bing Link: {link[:50]}...")
                            except Exception as ex:
                                print(f"     ⚠️ Bing Link Decode Error: {ex}")
                        
                        results.append(link)
                        if len(results) >= limit: break
            
            return results
        except Exception as e:
             print(f"   ❌ Bing Search failed: {e}")
             return [random.choice(self.SEED_URLS)] # Ultimate fallback

    def _is_listing_page(self, url: str) -> bool:
        """
        Heuristic to detect if a page is a list of methods (Method 2).
        e.g. 'category', 'list', 'tag', 'forum' in URL
        """
        keywords = ['list', 'category', 'tag', 'archive', 'forum', 'thread', 'page']
        return any(k in url.lower() for k in keywords)

    def _traverse_site(self, start_url: str):
        """
        Method 2 Implementation: Simple Depth-1 Traversal.
        Finds links in the page that look like content pages (not nav links).
        """
        try:
            # Add Referer to fool basic anti-bot checks
            traversal_headers = self.headers.copy()
            traversal_headers['Referer'] = start_url
            
            resp = requests.get(start_url, headers=traversal_headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract all links
            # Filter for links that are likely "Case Details" 
            # (Heuristic: Longer text, specific patterns)
            domain = urllib.parse.urlparse(start_url).netloc
            
            candidates = set()
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text().strip()
                
                # Normalize URL
                full_url = urllib.parse.urljoin(start_url, href)
                parsed_url = urllib.parse.urlparse(full_url)
                
                # Check domain constraint (stay on site)
                if parsed_url.netloc != domain:
                    continue
                    
                # Skip login/admin/tag/category index links
                lower_url = full_url.lower()
                if any(x in lower_url for x in ["login", "admin", "wp-admin", "search", "feed", "contact", "about"]):
                    continue
                
                # Heuristic: Is this a content page?
                # 1. Title is descriptive (len > 3)
                # 2. URL path is deep (e.g. /2023/10/title) or contains keywords
                is_content = False
                if len(text) > 4: 
                    is_content = True
                
                path_segments = [p for p in parsed_url.path.split('/') if p]
                if len(path_segments) >= 2 or any(k in lower_url for k in ['case', 'post', 'article', 'study', 'html']):
                    is_content = True
                    
                if is_content:
                    candidates.add(full_url)
            
            # Limit traversal to avoid explosion
            print(f"   ⛓️ Traversing top 5 sub-links from {len(candidates)} candidates...")
            for sub_url in list(candidates)[:5]: # Demo constrain
                if sub_url not in self.visited_urls:
                    self.visited_urls.add(sub_url)
                    self.hunter.hunt_from_url(sub_url)
                    time.sleep(1)
                    
        except Exception as e:
            print(f"   ❌ Traversal failed: {e}")

if __name__ == "__main__":
    miner = AutoMiner()
    miner.start_autopilot(max_cycles=1)
