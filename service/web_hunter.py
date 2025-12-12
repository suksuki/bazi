#!/usr/bin/env python3
"""
Web Hunter Module (V2 - Targeted Sniper)
Project Crimson Vein - Input Layer

Specialized strategies for high-quality Bazi data sources.
Target 1: Astro-Databank (The Gold Standard)
"""

import requests
import re
import urllib.parse
from datetime import datetime
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from service.sanitizer import Sanitizer
from service.processor import ContentProcessor

class WebHunter:
    def __init__(self):
        self.processor = ContentProcessor()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_adb_url = "https://www.astro.com/astro-databank"

    def hunt_target(self, query: str) -> bool:
        """
        Smart Hunt: Tries to guess the target URL based on the name query.
        Currently focused on ADB (Astro-Databank).
        """
        print(f"🎯 [Hunter] Tracking target: {query}")
        
        # Strategy A: Astro-Databank Direct URL Guessing
        # Format: "Musk, Elon" -> "Musk,_Elon"
        # If user types "Elon Musk", we flip it.
        
        candidates = []
        clean_q = query.strip()
        
        # 1. Exact match pass-through
        if "http" in clean_q:
            candidates.append(clean_q)
        else:
            # 2. Name permutation
            parts = clean_q.split(' ')
            if len(parts) >= 2:
                # "First Last" -> "Last, First"
                guess_1 = f"{parts[-1]},_{'_'.join(parts[:-1])}" # Jobs,_Steve
                candidates.append(f"{self.base_adb_url}/{guess_1}")
                
            # "Last First" -> "Last,_First" (Just in case)
            guess_2 = f"{parts[0]},_{'_'.join(parts[1:])}"
            candidates.append(f"{self.base_adb_url}/{guess_2}")

        # Execute Hunt
        for url in candidates:
            print(f"   🔫 Trying vector: {url} ...")
            try:
                if self._hunt_adb_page(url):
                    return True
            except Exception as e:
                print(f"   ❌ Missed: {e}")
                
        print("🤷 [Hunter] Target escaped. Try providing the exact URL.")
        return False

    def _hunt_adb_page(self, url: str) -> bool:
        """
        Specific Parser for Astro-Databank Wiki Pages.
        """
        if not BeautifulSoup:
            raise ImportError("BeautifulSoup is required for ADB parsing.")

        resp = requests.get(url, headers=self.headers, timeout=10)
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Validate it's a data page
        title = soup.find('h1', class_='firstHeading').text
        infobox = soup.find('table', class_='infobox')
        if not infobox:
            print("   ⚠️ Not a valid ADB data page (no infobox).")
            return False

        print(f"   ✅ Target Acquired: {title}")
        
        # 2. Extract Crude Data for Processor
        # We construct a synthetic text block that mimics a perfect case report
        # so our LLM Processor can easily digest it.
        
        content_buffer = []
        content_buffer.append(f"【Name】 {title}")
        content_buffer.append(f"【Source URL】 {url}")
        
        # Extract Rating
        rating_node = infobox.find('a', title=re.compile(r'Rodden Rating'))
        if rating_node:
            content_buffer.append(f"【Rodden Rating】 {rating_node.text.strip()}")
            
        # Extract Birth Data
        # ADB format varies, but usually in the infobox or first paragraph.
        # Let's dump all text from infobox.
        for row in infobox.find_all('tr'):
            text = row.get_text(" ", strip=True)
            if "born on" in text or "Time of Birth" in text:
                content_buffer.append(f"【Birth Data】 {text}")

        # Extract Biography & Events
        # ADB uses headers: "Biography", "Events", "Relationships"
        main_content = soup.find('div', class_='mw-parser-output')
        
        capture = False
        bio_text = ""
        events_text = ""
        
        for elem in main_content.children:
            if elem.name == 'h2':
                header = elem.get_text().lower()
                if 'biography' in header or 'events' in header or 'relationships' in header:
                    capture = True
                    content_buffer.append(f"\n【{elem.get_text().strip()}】")
                    continue
                else:
                    capture = False
            
            if capture and elem.name in ['p', 'ul']:
                text = elem.get_text().strip()
                if text: content_buffer.append(text)

        # 3. Assemble and Fire
        final_text = "\n".join(content_buffer)
        
        # Sanitize common ADB formatting noise
        final_text = final_text.replace("[..]", "").replace("Link to Wikipedia biography", "")
        
        print(f"   📦 Extracted {len(final_text)} chars of high-grade intel.")
        
        # Send to Processor
        self.processor.process_text(final_text, source_url=url)
        return True

    def hunt_from_url(self, url: str) -> bool:
        """
        Generic Hunter: Fetches content from ANY valid URL.
        Used for Method 1 (Search Results) & Method 3 (Discovery).
        """
        print(f"   🕸️ Generic Hunt: {url}")
        if "youtube.com" in url or "youtu.be" in url:
            print("   ⚠️ Skipping YouTube URL (VideoMiner territory).")
            return False
            
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                print(f"   ❌ Access Failed: {resp.status_code}")
                return False
                
            # Encoding fix
            if 'charset' not in resp.headers.get('content-type', '').lower():
                resp.encoding = resp.apparent_encoding
                
            text = self._extract_visible_text(resp.text)
            
            if len(text) < 100:
                print("   ⚠️ Content too short, skipping.")
                return False
                
            self.processor.process_text(text, source_url=url)
            print("   ✅ Generic capture successful.")
            return True
        except Exception as e:
            print(f"   ❌ Generic Hunt Error: {e}")
            return False

    def _extract_visible_text(self, html: str) -> str:
        if BeautifulSoup:
            soup = BeautifulSoup(html, 'html.parser')
            # Kill scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        else:
            # Fallback regex
            clean = re.sub('<[^<]+?>', '', html)
            return clean

if __name__ == "__main__":
    h = WebHunter()
    # Test with a known target
    h.hunt_target("Steve Jobs")
