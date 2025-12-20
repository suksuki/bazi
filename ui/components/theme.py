
"""
ui/components/theme.py
----------------------
🔮 Gypsy Fortune Teller Theme - Mystical Colors, Animations, and Icons
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 QUANTUM THEME - Gypsy Mystic Aesthetic
# ═══════════════════════════════════════════════════════════════════════════════

QUANTUM_THEME = {
    # --- Wood (Emerald Spirit / Forest Magic) ---
    "甲": {
        "color": "#22c55e", 
        "icon": "🌲", 
        "anim": "pulse-grow", 
        "grad": "linear-gradient(135deg, #1a4d2e 0%, #40e0d0 100%)"
    },
    "乙": {
        "color": "#40e0d0", 
        "icon": "🌿", 
        "anim": "sway", 
        "grad": "linear-gradient(to top, #0d5c4d 0%, #40e0d0 100%)"
    },
    "寅": {
        "color": "#10b981", 
        "icon": "🐅", 
        "anim": "pulse-grow", 
        "grad": "linear-gradient(to top, #064e3b 0%, #34d399 100%)"
    },
    "卯": {
        "color": "#6ee7b7", 
        "icon": "🐇", 
        "anim": "sway", 
        "grad": "linear-gradient(120deg, #059669 0%, #6ee7b7 100%)"
    },

    # --- Fire (Candle Flame / Passionate Spirit) ---
    "丙": {
        "color": "#ff9f43", 
        "icon": "☀️", 
        "anim": "spin-slow", 
        "grad": "radial-gradient(circle, #ff9f43, #c21e56)"
    },
    "丁": {
        "color": "#c21e56", 
        "icon": "🕯️", 
        "anim": "flicker", 
        "grad": "linear-gradient(to top, #c21e56 0%, #ff6b6b 100%)"
    },
    "巳": {
        "color": "#f97316", 
        "icon": "🐍", 
        "anim": "sway", 
        "grad": "linear-gradient(to right, #ea580c 0%, #fbbf24 100%)"
    },
    "午": {
        "color": "#ef4444", 
        "icon": "🐎", 
        "anim": "pulse-grow", 
        "grad": "linear-gradient(to right, #dc2626 0%, #f43f5e 100%)"
    },

    # --- Earth (Crystal Cave / Sacred Ground) ---
    "戊": {
        "color": "#a855f7", 
        "icon": "🏔️", 
        "anim": "stable", 
        "grad": "linear-gradient(to top, #581c87 0%, #a855f7 100%)"
    },
    "己": {
        "color": "#c084fc", 
        "icon": "🔮", 
        "anim": "stable", 
        "grad": "linear-gradient(to top, #6b21a8 0%, #d8b4fe 100%)"
    },
    "辰": {
        "color": "#ffd700", 
        "icon": "🐲", 
        "anim": "float", 
        "grad": "linear-gradient(to top, #b8860b 0%, #ffd700 100%)"
    },
    "戌": {
        "color": "#a78bfa", 
        "icon": "🌋", 
        "anim": "rumble", 
        "grad": "linear-gradient(to right, #2d1b4e 0%, #7c3aed 100%)"
    },
    "丑": {
        "color": "#facc15", 
        "icon": "🐂", 
        "anim": "stable", 
        "grad": "linear-gradient(to top, #ca8a04 0%, #fde047 100%)"
    },
    "未": {
        "color": "#fb923c", 
        "icon": "🐑", 
        "anim": "stable", 
        "grad": "linear-gradient(120deg, #ea580c 0%, #fbbf24 100%)"
    },

    # --- Metal (Silver Moon / Precious Treasure) ---
    "庚": {
        "color": "#e8e8f0", 
        "icon": "⚔️", 
        "anim": "flash", 
        "grad": "linear-gradient(to top, #94a3b8 0%, #e8e8f0 100%)"
    },
    "辛": {
        "color": "#ffd700", 
        "icon": "💎", 
        "anim": "sparkle", 
        "grad": "linear-gradient(135deg, #b8860b 0%, #ffd700 50%, #fff8dc 100%)"
    },
    "申": {
        "color": "#cbd5e1", 
        "icon": "🐵", 
        "anim": "swing", 
        "grad": "linear-gradient(to top, #475569 0%, #94a3b8 100%)"
    },
    "酉": {
        "color": "#f1f5f9", 
        "icon": "🐓", 
        "anim": "strut", 
        "grad": "linear-gradient(to top, #94a3b8 0%, #f8fafc 100%)"
    },

    # --- Water (Mystic Ocean / Deep Secrets) ---
    "壬": {
        "color": "#40e0d0", 
        "icon": "🌊", 
        "anim": "wave", 
        "grad": "linear-gradient(to top, #0d5c4d 0%, #40e0d0 100%)"
    },
    "癸": {
        "color": "#a855f7", 
        "icon": "☁️", 
        "anim": "drift", 
        "grad": "linear-gradient(to top, #581c87 0%, #c084fc 100%)"
    },
    "子": {
        "color": "#3b82f6", 
        "icon": "🐀", 
        "anim": "scurry", 
        "grad": "linear-gradient(15deg, #1e3a8a 0%, #60a5fa 100%)"
    },
    "亥": {
        "color": "#8b5cf6", 
        "icon": "🐖", 
        "anim": "float", 
        "grad": "linear-gradient(to top, #4c1d95 0%, #a78bfa 100%)"
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🌙 Mystical Navigation Icons
# ═══════════════════════════════════════════════════════════════════════════════

MYSTIC_ICONS = {
    "prediction": "🔮",
    "wealth": "💰",
    "evolution": "🌙",
    "mining": "📜",
    "quantum": "✨",
    "cinema": "🌟",
    "training": "🕯️",
    "config": "⚙️",
    "architect": "⚡",
    "crystal_ball": "🔮",
    "moon": "🌙",
    "star": "⭐",
    "candle": "🕯️",
    "sparkle": "✨",
    "tarot": "🎴",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 Mystical Gradient Palette
# ═══════════════════════════════════════════════════════════════════════════════

MYSTIC_GRADIENTS = {
    "midnight": "linear-gradient(180deg, #0d0015 0%, #1a0a2e 100%)",
    "velvet": "linear-gradient(145deg, #2d1b4e 0%, #1a0a2e 100%)",
    "gold_shimmer": "linear-gradient(90deg, #b8860b 0%, #ffd700 50%, #b8860b 100%)",
    "crystal": "radial-gradient(circle at 30% 30%, rgba(255,255,255,0.3), rgba(168,85,247,0.5), rgba(26,10,46,0.9))",
    "candle_glow": "radial-gradient(circle, #ff9f43 0%, rgba(255,159,67,0) 70%)",
    "starfield": "radial-gradient(ellipse at 50% 50%, rgba(168,85,247,0.2) 0%, transparent 70%)",
    "tarot_border": "linear-gradient(90deg, #c21e56, #ffd700, #40e0d0, #a855f7)",
}

# ═══════════════════════════════════════════════════════════════════════════════
# ✨ Magical Animation Definitions
# ═══════════════════════════════════════════════════════════════════════════════

MYSTIC_ANIMATIONS = {
    "shimmer": "shimmer 3s linear infinite",
    "glow": "crystal-pulse 4s ease-in-out infinite",
    "float": "float 3s ease-in-out infinite",
    "flicker": "flicker 2s ease-in-out infinite",
    "twinkle": "twinkle 2s ease-in-out infinite",
    "moon_glow": "moon-glow 3s ease-in-out infinite",
}


def get_theme(char):
    """Get theme dict for a character (Stem/Branch)."""
    return QUANTUM_THEME.get(char, {"color": "#FFF", "icon": "❓", "anim": "none", "grad": "none"})


def get_nature_color(char):
    """Helper to get just the color."""
    return get_theme(char)["color"]


def get_mystic_icon(name):
    """Get a mystical icon by name."""
    return MYSTIC_ICONS.get(name, "🔮")


def get_mystic_gradient(name):
    """Get a mystical gradient by name."""
    return MYSTIC_GRADIENTS.get(name, MYSTIC_GRADIENTS["midnight"])
