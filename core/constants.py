# core/constants.py
"""
Antigravity V3.0 Constants
Defining the Hidden Energy (Grave/Treasury Theory)
"""

# The Four Graves / Treasuries (四墓库)
# Structure: 
#   - type: The element of the tomb (what is stored).
#   - stems: The hidden heavenly stems.
#       - main: The Box (Earth itself).
#       - residual: The lingering energy from the previous season.
#       - tomb: The Treasure (The element being stored).

GRAVE_TREASURY_CONFIG = {
    '辰': {
        'name_cn': 'Dragon',
        'type': 'water_tomb',
        'element': 'water', # The element associated with the tomb (Water Tomb)
        'stems': {
            'main': '戊',      # Wu Earth (Main Qi / The Box)
            'residual': '乙',  # Yi Wood (Residual from Spring)
            'tomb': '癸'       # Gui Water (The Treasury / Tomb Gas)
        }
    },
    '戌': {
        'name_cn': 'Dog',
        'type': 'fire_tomb',
        'element': 'fire',
        'stems': {
            'main': '戊',      # Wu Earth (Main Qi / The Box)
            'residual': '辛',  # Xin Metal (Residual from Autumn)
            'tomb': '丁'       # Ding Fire (The Treasury / Tomb Gas)
        }
    },
    '丑': {
        'name_cn': 'Ox',
        'type': 'metal_tomb',
        'element': 'metal',
        'stems': {
            'main': '己',      # Ji Earth (Main Qi / The Box)
            'residual': '癸',  # Gui Water (Residual from Winter)
            'tomb': '辛'       # Xin Metal (The Treasury / Tomb Gas)
        }
    },
    '未': {
        'name_cn': 'Sheep',
        'type': 'wood_tomb',
        'element': 'wood',
        'stems': {
            'main': '己',      # Ji Earth (Main Qi / The Box)
            'residual': '丁',  # Ding Fire (Residual from Summer)
            'tomb': '乙'       # Yi Wood (The Treasury / Tomb Gas)
        }
    }
}

# Full Hidden Stems Mapping (12 Earthly Branches) for reference and QuantumEngine
HIDDEN_STEMS_MAP = {
    '子': {'main': '癸', 'hidden': ['癸']},
    '丑': GRAVE_TREASURY_CONFIG['丑']['stems'],
    '寅': {'main': '甲', 'hidden': ['甲', '丙', '戊']},
    '卯': {'main': '乙', 'hidden': ['乙']},
    '辰': GRAVE_TREASURY_CONFIG['辰']['stems'],
    '巳': {'main': '丙', 'hidden': ['丙', '庚', '戊']},
    '午': {'main': '丁', 'hidden': ['丁', '己']},
    '未': GRAVE_TREASURY_CONFIG['未']['stems'],
    '申': {'main': '庚', 'hidden': ['庚', '壬', '戊']},
    '酉': {'main': '辛', 'hidden': ['辛']},
    '戌': GRAVE_TREASURY_CONFIG['戌']['stems'],
    '亥': {'main': '壬', 'hidden': ['壬', '甲']},
}
