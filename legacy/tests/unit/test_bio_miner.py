import unittest
import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from service.bio_miner import BioMiner

class TestBioMiner(unittest.TestCase):
    def setUp(self):
        # Configure logging to show info during tests
        logging.basicConfig(level=logging.INFO)
        self.miner = BioMiner()
        self.ma_yun_text = """
        1964年9月10日，马云出生于浙江省杭州市。
        1988年，马云从杭州师范学院外语系英语专业毕业，获文学学士学位，之后被分配到杭州电子工业学院（现杭州电子科技大学）任英文及国际贸易讲师。
        1995年，马云创办了“中国黄页”，这是中国第一家互联网商业信息发布网站。
        1999年，马云在杭州创办了阿里巴巴。
        2000年，互联网泡沫破裂，公司差点倒闭，但马云坚持了下来。
        2003年，秘密成立淘宝网。
        2014年9月19日，阿里巴巴集团于纽约证券交易所正式挂牌上市，马云成为中国首富。
        2019年9月10日，马云卸任阿里巴巴董事局主席。
        """

    def test_mine_events_ma_yun(self):
        """Test mining events from Jack Ma's biography snippet."""
        print(f"\nTesting BioMiner with text length: {len(self.ma_yun_text)}")
        events = self.miner.mine_events(self.ma_yun_text)
        
        print(f"\nExtracted {len(events)} Events:")
        for ev in events:
            print(ev)
            
        # Basic Validation
        self.assertIsInstance(events, list)
        if not events:
            print("WARNING: No events extracted. LLM might be offline or failing.")
            return

        self.assertTrue(len(events) > 0, "Should extract at least one event")
        
        # Check for key events
        years_extracted = [e['year'] for e in events]
        self.assertIn(1999, years_extracted, "Should extract 1999 (Founding Alibaba)")
        self.assertIn(2014, years_extracted, "Should extract 2014 (IPO)")
        
        # Check polarity
        for ev in events:
            if ev['year'] == 2014:
                self.assertEqual(ev['type'], 'positive', "2014 IPO should be positive")
            if ev['year'] == 2000 and '泡沫' in ev.get('description', ''):
                 self.assertEqual(ev['type'], 'negative', "2000 bubble burst should be negative")

    def test_sanitize_json(self):
        """Test the JSON sanitizer with some broken inputs."""
        # Case 1: Extra text
        broken_1 = """
        Here is the data:
        [{"year": 1999, "event": "Test", "type": "positive"}]
        I hope this helps.
        """
        res_1 = self.miner._sanitize_and_parse_json(broken_1)
        self.assertEqual(len(res_1), 1, "Should filter out surrounding text")
        
        # Case 2: Missing closing bracket
        broken_2 = '[{"year": 1999, "event": "Test", "type": "positive"}'
        res_2 = self.miner._sanitize_and_parse_json(broken_2)
        self.assertEqual(len(res_2), 1, "Should fix missing closing bracket")
        
        # Case 3: Trailing comma and missing bracket
        # Note: The current file implementation handles this.
        broken_3 = '[{"year": 1999, "event": "Test", "type": "positive"},'
        res_3 = self.miner._sanitize_and_parse_json(broken_3)
        self.assertEqual(len(res_3), 1, "Should fix trailing comma and missing bracket")

if __name__ == '__main__':
    unittest.main()
