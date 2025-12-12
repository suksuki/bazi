
from learning.miners.china95 import China95Parser
import json

# MOCK DATA: A structure representing a crawled thread
# Thread ID: 1024
# Title: 看看我的财运
mock_thread_china95 = [
    # Post 1: OP
    {
        "user": "DragonUser88",
        "content": """
        大师们好，我是新人。
        出生公历：1988年11月14日18时37分(北京时间)。
        乾造   戊      癸      丁      己 (日空申酉)
               辰      亥      卯      酉
        排大运：
        甲子 乙丑 丙寅...
        请问2018年怎么样？
        """
    },
    # Post 2: Master A
    {
        "user": "MasterZhang",
        "content": "2018年戊戌，辰戌冲，恐怕有变动，或者长辈有事。"
    },
    # Post 3: OP Reply (The Feedback Anchor!)
    {
        "user": "DragonUser88",
        "content": "反馈大师：确实准！2018年父亲去世了，而且工作也调动了，非常动荡。"
    },
    # Post 4: Master B
    {
        "user": "GodEye",
        "content": "节哀。"
    }
]

# Run Parser
parser = China95Parser()
result = parser.parse_thread(mock_thread_china95)

print("--- Mining Result (China95 Strategy) ---")
print(json.dumps(result, indent=2, ensure_ascii=False))

# Validation
if result['data_quality_score'] > 0.8:
    print("\n✅ DATA ACCEPTED: High Quality Feedback Found.")
else:
    print("\n❌ DATA REJECTED: Low Quality.")
