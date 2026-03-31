"""
QGA 地理城市映射 (Geo City Map)
===============================
存储全球主要城市的地理系数与元素亲和力数据
Extracted from: ui/pages/quantum_lab.py
"""

# Format: "城市 (City)": (geo_factor, "element_affinity")
# geo_factor: 0.7-1.5 based on climate/geography (>1 = stronger field, <1 = weaker)
GEO_CITY_MAP = {
    # === 中国直辖市/一线城市 (Tier-1 Cities) ===
    "北京 (Beijing)": (1.15, "Fire/Earth"),
    "上海 (Shanghai)": (1.08, "Water/Metal"),
    "深圳 (Shenzhen)": (1.12, "Fire/Water"),
    "广州 (Guangzhou)": (1.10, "Fire"),
    "天津 (Tianjin)": (1.05, "Water/Earth"),
    "重庆 (Chongqing)": (0.95, "Water/Fire"),
    
    # === 省会城市 (Provincial Capitals) ===
    # 华北 (North China)
    "石家庄 (Shijiazhuang)": (1.02, "Earth"),
    "太原 (Taiyuan)": (0.98, "Metal/Earth"),
    "呼和浩特 (Hohhot)": (0.88, "Metal/Water"),
    
    # 东北 (Northeast)
    "沈阳 (Shenyang)": (1.05, "Water/Metal"),
    "长春 (Changchun)": (1.00, "Water/Wood"),
    "哈尔滨 (Harbin)": (0.95, "Water"),
    
    # 华东 (East China)
    "南京 (Nanjing)": (1.08, "Fire/Water"),
    "杭州 (Hangzhou)": (1.10, "Water/Wood"),
    "合肥 (Hefei)": (1.02, "Earth/Water"),
    "福州 (Fuzhou)": (1.05, "Water/Wood"),
    "南昌 (Nanchang)": (1.00, "Fire/Water"),
    "济南 (Jinan)": (1.03, "Water/Earth"),
    
    # 华中 (Central China)
    "郑州 (Zhengzhou)": (1.05, "Earth/Fire"),
    "武汉 (Wuhan)": (1.08, "Water/Fire"),
    "长沙 (Changsha)": (1.06, "Fire/Water"),
    
    # 华南 (South China)
    "南宁 (Nanning)": (1.00, "Wood/Water"),
    "海口 (Haikou)": (0.92, "Water/Fire"),
    
    # 西南 (Southwest)
    "成都 (Chengdu)": (0.95, "Earth/Wood"),
    "贵阳 (Guiyang)": (0.90, "Wood/Water"),
    "昆明 (Kunming)": (0.88, "Wood/Fire"),
    "拉萨 (Lhasa)": (0.75, "Metal/Earth"),
    
    # 西北 (Northwest)
    "西安 (Xi'an)": (1.05, "Metal/Earth"),
    "兰州 (Lanzhou)": (0.92, "Metal/Water"),
    "西宁 (Xining)": (0.85, "Water/Metal"),
    "银川 (Yinchuan)": (0.88, "Metal/Earth"),
    "乌鲁木齐 (Urumqi)": (0.80, "Metal/Fire"),
    
    # === 其他重要城市 (Other Major Cities) ===
    "苏州 (Suzhou)": (1.10, "Water/Wood"),
    "无锡 (Wuxi)": (1.08, "Water/Metal"),
    "宁波 (Ningbo)": (1.06, "Water"),
    "青岛 (Qingdao)": (1.08, "Water/Wood"),
    "大连 (Dalian)": (1.05, "Water/Metal"),
    "厦门 (Xiamen)": (1.08, "Water/Fire"),
    "珠海 (Zhuhai)": (1.05, "Water/Fire"),
    "东莞 (Dongguan)": (1.08, "Fire/Metal"),
    "佛山 (Foshan)": (1.05, "Fire/Metal"),
    
    # === 港澳台 (HK/Macau/Taiwan) ===
    "香港 (Hong Kong)": (1.20, "Water/Metal"),
    "澳门 (Macau)": (1.10, "Water/Fire"),
    "台北 (Taipei)": (1.15, "Water/Wood"),
    "高雄 (Kaohsiung)": (1.08, "Fire/Water"),
    
    # === 亚洲城市 (Asian Cities) ===
    "东京 (Tokyo)": (1.20, "Water/Metal"),
    "大阪 (Osaka)": (1.12, "Water/Fire"),
    "首尔 (Seoul)": (1.15, "Metal/Water"),
    "新加坡 (Singapore)": (0.85, "Fire/Water"),
    "吉隆坡 (Kuala Lumpur)": (0.90, "Fire/Wood"),
    "曼谷 (Bangkok)": (0.88, "Fire/Water"),
    "马尼拉 (Manila)": (0.92, "Fire/Water"),
    "雅加达 (Jakarta)": (0.85, "Fire/Wood"),
    "河内 (Hanoi)": (0.95, "Water/Wood"),
    "胡志明市 (Ho Chi Minh)": (0.92, "Fire/Water"),
    "孟买 (Mumbai)": (0.95, "Fire/Water"),
    "新德里 (New Delhi)": (1.00, "Fire/Earth"),
    "迪拜 (Dubai)": (0.80, "Fire/Metal"),
    
    # === 欧洲城市 (European Cities) ===
    "伦敦 (London)": (1.15, "Water/Metal"),
    "巴黎 (Paris)": (1.12, "Metal/Water"),
    "柏林 (Berlin)": (1.08, "Metal/Earth"),
    "法兰克福 (Frankfurt)": (1.10, "Metal/Earth"),
    "阿姆斯特丹 (Amsterdam)": (1.05, "Water"),
    "苏黎世 (Zurich)": (1.08, "Metal/Water"),
    "米兰 (Milan)": (1.05, "Fire/Metal"),
    "莫斯科 (Moscow)": (1.00, "Water/Metal"),
    
    # === 北美城市 (North American Cities) ===
    "纽约 (New York)": (1.25, "Metal/Water"),
    "洛杉矶 (Los Angeles)": (1.15, "Fire/Metal"),
    "旧金山 (San Francisco)": (1.18, "Water/Metal"),
    "西雅图 (Seattle)": (1.12, "Water/Wood"),
    "芝加哥 (Chicago)": (1.10, "Metal/Water"),
    "多伦多 (Toronto)": (1.12, "Water/Metal"),
    "温哥华 (Vancouver)": (1.18, "Water/Wood"),
    
    # === 大洋洲城市 (Oceanian Cities) ===
    "悉尼 (Sydney)": (0.90, "Fire/Earth"),
    "墨尔本 (Melbourne)": (0.92, "Water/Earth"),
    "奥克兰 (Auckland)": (0.88, "Water/Wood"),
}
