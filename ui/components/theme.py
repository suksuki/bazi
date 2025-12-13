
"""
ui/components/theme.py
----------------------
Manages colors, animations, and visual themes for the Quantum UI.
"""

QUANTUM_THEME = {
    # --- Wood (Growth / Networking) ---
    "甲": {"color": "#4ade80", "icon": "🌲", "anim": "pulse-grow", "grad": "linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d)"}, # Green 400
    "乙": {"color": "#86efac", "icon": "🌿", "anim": "sway", "grad": "linear-gradient(to top, #0ba360 0%, #3cba92 100%)"},
    "寅": {"color": "#22c55e", "icon": "🐅", "anim": "pulse-fast", "grad": "linear-gradient(to top, #09203f 0%, #537895 100%)"}, # Green 500
    "卯": {"color": "#a3e635", "icon": "🐇", "anim": "bounce", "grad": "linear-gradient(120deg, #d4fc79 0%, #96e6a1 100%)"},

    # --- Fire (Radiation / Focus) ---
    "丙": {"color": "#fb923c", "icon": "☀️", "anim": "spin-slow", "grad": "radial-gradient(circle, #ff9966, #ff5e62)"}, # Orange 400
    "丁": {"color": "#f472b6", "icon": "🕯️", "anim": "flicker", "grad": "linear-gradient(to top, #f43b47 0%, #453a94 100%)"}, # Pink 400
    "巳": {"color": "#fdba74", "icon": "🐍", "anim": "slither", "grad": "linear-gradient(to right, #f83600 0%, #f9d423 100%)"},
    "午": {"color": "#f87171", "icon": "🐎", "anim": "gallop", "grad": "linear-gradient(to right, #ff8177 0%, #ff867a 0%, #ff8c7f 21%, #f99185 52%, #cf556c 78%, #b12a5b 100%)"}, # Red 400

    # --- Earth (Mass / Matrix) ---
    "戊": {"color": "#a8a29e", "icon": "🏔️", "anim": "stable", "grad": "linear-gradient(to top, #c79081 0%, #dfa579 100%)"}, # Stone 400
    "己": {"color": "#e7e5e4", "icon": "🧱", "anim": "stable", "grad": "linear-gradient(to top, #e6b980 0%, #eacda3 100%)"},
    "辰": {"color": "#84cc16", "icon": "🐲", "anim": "float", "grad": "linear-gradient(to top, #9be15d 0%, #00e3ae 100%)"}, 
    "戌": {"color": "#fda4af", "icon": "🌋", "anim": "rumble", "grad": "linear-gradient(to right, #434343 0%, black 100%)"}, 
    "丑": {"color": "#fde047", "icon": "🐂", "anim": "stable", "grad": "linear-gradient(to top, #50cc7f 0%, #f5d100 100%)"}, # Yellow 300
    "未": {"color": "#fdba74", "icon": "🐑", "anim": "stable", "grad": "linear-gradient(120deg, #f6d365 0%, #fda085 100%)"}, 

    # --- Metal (Impact / Order) ---
    "庚": {"color": "#cbd5e1", "icon": "⚔️", "anim": "flash", "grad": "linear-gradient(to top, #cfd9df 0%, #e2ebf0 100%)"}, # Slate 300
    "辛": {"color": "#fde047", "icon": "💎", "anim": "sparkle", "grad": "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)"}, # Gold
    "申": {"color": "#94a3b8", "icon": "🐵", "anim": "swing", "grad": "linear-gradient(to top, #30cfd0 0%, #330867 100%)"}, # Slate 400
    "酉": {"color": "#e2e8f0", "icon": "🐓", "anim": "strut", "grad": "linear-gradient(to top, #cd9cf2 0%, #f6f3ff 100%)"}, # Slate 200

    # --- Water (Flow / Permeability) ---
    "壬": {"color": "#38bdf8", "icon": "🌊", "anim": "wave", "grad": "linear-gradient(to top, #3b41c5 0%, #a981bb 49%, #ffc8a9 100%)"}, # Sky 400
    "癸": {"color": "#7dd3fc", "icon": "☁️", "anim": "drift", "grad": "linear-gradient(to top, #a18cd1 0%, #fbc2eb 100%)"}, # Sky 300
    "子": {"color": "#60a5fa", "icon": "🐀", "anim": "scurry", "grad": "linear-gradient(15deg, #13547a 0%, #80d0c7 100%)"}, # Blue 400
    "亥": {"color": "#818cf8", "icon": "🐖", "anim": "float", "grad": "linear-gradient(to top, #4fb576 0%, #44a08d 24%, #2b88aa 52%, #0f5f87 76%, #0d2f4a 100%)"}, # Indigo 400
}

def get_theme(char):
    """Get theme dict for a character (Stem/Branch)."""
    return QUANTUM_THEME.get(char, {"color": "#FFF", "icon": "❓", "anim": "none", "grad": "none"})

def get_nature_color(char):
    """Helper to get just the color."""
    return get_theme(char)["color"]
