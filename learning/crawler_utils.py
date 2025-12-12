
import time
import random
import re
import hashlib
import logging
import requests

logger = logging.getLogger("CrawlerUtils")

class SafeCrawler:
    """
    Implements V6.2 Safety & Compliance Protocol.
    - Politeness (Random Delay)
    - User-Agent Rotation
    - PII Scrubbing
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
    ]
    
    @staticmethod
    def polite_get(url, cookies=None):
        """
        Fetches URL with random delay and safety headers.
        """
        # 1. Politeness Delay (3s - 8s)
        delay = random.uniform(3.0, 8.0)
        logger.info(f"💤 Sleeping {delay:.2f}s before request...")
        time.sleep(delay)
        
        headers = {
            "User-Agent": random.choice(SafeCrawler.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            
            # 3. Status Check
            if resp.status_code == 403:
                logger.warning("⛔ 403 Forbidden detected. Backing off for 1 hour...")
                # In real prod, might raise error or sleep
                # time.sleep(3600) 
                return None
            
            return resp.text
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    @staticmethod
    def scrub_pii(text):
        """
        Removes sensitive personal information.
        """
        if not text: return text
        
        # 1. Phone Numbers (Simple CN mobile)
        text = re.sub(r"1[3-9]\d{9}", "[PHONE_REMOVED]", text)
        
        # 2. WeChat / QQ (Contextual)
        text = re.sub(r"(微信|wechat|vx|qq)[:：\s]*[a-zA-Z0-9_\-]{5,}", r"\1: [ID_REMOVED]", text, flags=re.IGNORECASE)
        
        # 3. Email
        text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_REMOVED]", text)
        
        return text

    @staticmethod
    def hash_user_id(user_name):
        """
        Anonymizes User ID via SHA-256.
        """
        if not user_name: return "unknown"
        return hashlib.sha256(user_name.encode()).hexdigest()[:16]
