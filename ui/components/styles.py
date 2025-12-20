
"""
ui/components/styles.py
-----------------------
CSS styles for the Gypsy Fortune Teller / Mystical Theme.
"""

def get_glassmorphism_css():
    """Returns the main card styles (Gypsy Mystic Theme)."""
    return """
    <style>
    /* ═══════════════════════════════════════════════════════════
       🔮 Tarot Card Styles - Gypsy Fortune Teller Theme
       ═══════════════════════════════════════════════════════════ */

    /* 1. Narrative Card (Tarot Card Fragment) */
    .narrative-card {
        position: relative;
        padding: 28px;
        border-radius: 16px;
        border: 2px solid rgba(255,215,0,0.3);
        box-shadow: 
            0 8px 32px rgba(168,85,247,0.3),
            inset 0 1px 0 rgba(255,255,255,0.1);
        margin-bottom: 24px;
        background: linear-gradient(145deg, 
            rgba(45,27,78,0.95) 0%, 
            rgba(26,10,46,0.98) 100%);
        overflow: hidden;
    }
    
    .narrative-card::before {
        content: '✧';
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 1.2rem;
        color: rgba(255,215,0,0.6);
        animation: twinkle 2s infinite;
    }
    
    .narrative-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, 
            #c21e56, #ffd700, #40e0d0, #a855f7);
    }
    
    .narrative-card:hover {
        transform: translateY(-4px);
        box-shadow: 
            0 12px 40px rgba(168,85,247,0.4),
            0 0 60px rgba(255,215,0,0.15);
        border-color: #ffd700;
    }

    /* 2. Card Types / Elemental Themes */
    /* Mountain Alliance - Earth Crystal */
    .card-mountain {
        background: linear-gradient(135deg, 
            rgba(139,69,19,0.3) 0%, 
            rgba(45,27,78,0.95) 100%);
        border-top: 4px solid #ffd700;
    }
    .icon-mountain {
        font-size: 36px;
        color: #ffd700;
        filter: drop-shadow(0 0 10px rgba(255,215,0,0.5));
    }

    /* Shield - Mystic Water */
    .card-shield {
        background: linear-gradient(135deg, 
            rgba(64,224,208,0.2) 0%, 
            rgba(45,27,78,0.95) 100%);
        border-top: 4px solid #40e0d0;
    }
    .icon-shield {
        font-size: 36px;
        color: #40e0d0;
        filter: drop-shadow(0 0 10px rgba(64,224,208,0.5));
    }

    /* Flow - Spirit Wind */
    .card-flow {
        background: linear-gradient(135deg, 
            rgba(168,85,247,0.2) 0%, 
            rgba(45,27,78,0.95) 100%);
        border-top: 4px solid #a855f7;
    }
    .icon-flow {
        font-size: 36px;
        color: #a855f7;
        filter: drop-shadow(0 0 10px rgba(168,85,247,0.5));
    }

    /* Danger - Blood Moon */
    .card-danger {
        background: linear-gradient(135deg, 
            rgba(194,30,86,0.3) 0%, 
            rgba(45,27,78,0.95) 100%);
        border-top: 4px solid #c21e56;
    }

    /* 3. Typography (Mystical Serif) */
    .card-title {
        font-family: 'Cinzel Decorative', 'Ma Shan Zheng', cursive;
        font-weight: 500;
        font-size: 1.4rem;
        margin-bottom: 8px;
        color: #ffd700;
        letter-spacing: 2px;
        text-shadow: 0 0 15px rgba(255,215,0,0.4);
    }
    .card-subtitle {
        font-family: 'Philosopher', 'Noto Serif SC', serif;
        font-size: 1rem;
        color: #e8e8f0;
        margin-bottom: 16px;
        opacity: 0.9;
    }
    .card-impact {
        font-family: 'Philosopher', serif;
        font-size: 0.9rem;
        padding: 6px 14px;
        border-radius: 20px;
        background: linear-gradient(145deg, 
            rgba(168,85,247,0.3), 
            rgba(194,30,86,0.3));
        display: inline-block;
        color: #ffd700;
        border: 1px solid rgba(255,215,0,0.4);
        box-shadow: 0 0 15px rgba(168,85,247,0.2);
    }
    
    @keyframes twinkle {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 1; }
    }
    </style>
    """

def get_animation_css():
    """Returns animation and token styles (Crystal Ball / Mystic Seal)."""
    return """
    <style>
        /* ═══════════════════════════════════════════════════════════
           🔮 Mystic Animations - Gypsy Fortune Teller Theme
           ═══════════════════════════════════════════════════════════ */
        
        /* --- Celestial Animations --- */
        @keyframes sway { 
            0% { transform: rotate(-2deg); } 
            50% { transform: rotate(2deg); } 
            100% { transform: rotate(-2deg); } 
        }
        @keyframes pulse-grow { 
            0% { transform: scale(1); opacity: 0.9; } 
            50% { transform: scale(1.05); opacity: 1; } 
            100% { transform: scale(1); opacity: 0.9; } 
        }
        @keyframes flicker { 
            0% { opacity: 0.8; filter: brightness(0.9); } 
            25% { opacity: 1; filter: brightness(1.1); } 
            50% { opacity: 0.85; filter: brightness(0.95); } 
            75% { opacity: 1; filter: brightness(1.05); } 
            100% { opacity: 0.8; filter: brightness(0.9); } 
        }
        @keyframes spin-slow { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }
        @keyframes wave { 
            0% { transform: translateY(0) rotate(0); } 
            25% { transform: translateY(-3px) rotate(1deg); }
            50% { transform: translateY(0) rotate(0); } 
            75% { transform: translateY(3px) rotate(-1deg); }
            100% { transform: translateY(0) rotate(0); } 
        }
        @keyframes crystal-pulse {
            0%, 100% { 
                box-shadow: 0 0 20px rgba(168,85,247,0.4), 
                            0 0 40px rgba(255,215,0,0.2); 
            }
            50% { 
                box-shadow: 0 0 35px rgba(168,85,247,0.7), 
                            0 0 70px rgba(255,215,0,0.4); 
            }
        }
        @keyframes moon-glow {
            0%, 100% { filter: drop-shadow(0 0 8px rgba(232,232,240,0.5)); }
            50% { filter: drop-shadow(0 0 20px rgba(232,232,240,0.9)); }
        }
        
        /* --- Pillar Card (Celestial Tablet) --- */
        .pillar-card {
            background: linear-gradient(145deg, 
                rgba(45,27,78,0.9) 0%, 
                rgba(26,10,46,0.95) 100%);
            border-radius: 16px;
            padding: 20px 15px;
            text-align: center;
            border: 2px solid rgba(255,215,0,0.25);
            box-shadow: 
                0 8px 32px rgba(168,85,247,0.2),
                inset 0 0 40px rgba(0,0,0,0.5);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .pillar-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                #c21e56, #ffd700, #40e0d0);
        }
        
        .pillar-card:hover {
            border-color: #ffd700;
            box-shadow: 
                0 0 30px rgba(255,215,0,0.3),
                0 12px 40px rgba(168,85,247,0.3);
            transform: translateY(-5px);
        }
        
        .pillar-title {
            font-family: 'Cinzel Decorative', cursive;
            font-size: 1.1em;
            color: #40e0d0;
            margin-bottom: 15px;
            border-bottom: 1px solid rgba(255,215,0,0.3);
            padding-bottom: 8px;
            letter-spacing: 1px;
        }
        
        /* --- Crystal Ball Token (Mystic Orb) --- */
        .quantum-token {
            display: inline-flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            margin: 8px auto;
            position: relative;
            
            /* Crystal Ball Effect */
            background: radial-gradient(circle at 30% 30%, 
                rgba(255,255,255,0.25) 0%, 
                rgba(168,85,247,0.4) 40%, 
                rgba(26,10,46,0.9) 100%);
            border: 3px solid rgba(255,215,0,0.5);
            box-shadow: 
                0 0 25px rgba(168,85,247,0.5),
                inset 0 0 30px rgba(255,255,255,0.1),
                0 8px 20px rgba(0,0,0,0.5);
            animation: crystal-pulse 4s ease-in-out infinite;
        }
        
        .token-char {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.5em;
            color: #FFF;
            text-shadow: 
                0 0 10px rgba(255,215,0,0.8),
                0 2px 4px rgba(0,0,0,0.9);
            z-index: 2;
        }
        
        .token-icon {
            font-size: 0.9em;
            position: absolute;
            top: 5px;
            right: 5px;
            opacity: 0.9;
            z-index: 3;
            animation: moon-glow 3s ease-in-out infinite;
        }
        
        /* --- Hidden Stems (Small Mystic Seals) --- */
        .hidden-container {
            display: flex;
            justify-content: center;
            gap: 10px; 
            margin-top: 18px;
            padding-top: 12px;
            border-top: 1px dashed rgba(255,215,0,0.3);
        }
        
        .hidden-token {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            font-family: 'Noto Serif SC', serif;
            font-size: 0.85em;
            color: #FFF;
            
            display: flex;
            align-items: center;
            justify-content: center;
            
            background: linear-gradient(135deg, 
                rgba(168,85,247,0.4), 
                rgba(194,30,86,0.4));
            box-shadow: 
                0 0 10px rgba(168,85,247,0.3),
                0 2px 4px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,215,0,0.4);
            cursor: help;
            transition: all 0.3s ease;
        }
        
        .hidden-token:hover {
            transform: scale(1.2);
            box-shadow: 0 0 20px rgba(255,215,0,0.5);
            border-color: #ffd700;
        }
        
        /* Day Master Glow (The Chosen One) */
        .dm-glow {
            border-color: #ffd700 !important;
            box-shadow: 
                0 0 30px rgba(255,215,0,0.6),
                0 0 60px rgba(168,85,247,0.4) !important;
            animation: crystal-pulse 2s ease-in-out infinite !important;
        }
    </style>
    """

def get_bazi_table_css():
    """Returns the CSS for the Bazi Table (Fortune Teller Table)."""
    return """
    <style>
        /* ═══════════════════════════════════════════════════════════
           🔮 Bazi Table - Fortune Teller Spread
           ═══════════════════════════════════════════════════════════ */
        
        .bazi-box {
            background: linear-gradient(145deg, 
                rgba(45,27,78,0.9) 0%, 
                rgba(26,10,46,0.95) 100%);
            padding: 20px;
            border-radius: 16px;
            text-align: center;
            font-family: 'Philosopher', 'Noto Serif SC', serif;
            box-shadow: 
                0 8px 32px rgba(168,85,247,0.3),
                inset 0 0 40px rgba(0,0,0,0.4);
            border: 2px solid rgba(255,215,0,0.3);
            position: relative;
        }
        
        .bazi-box::before {
            content: '🌙';
            position: absolute;
            top: -15px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 1.5rem;
            animation: moon-glow 3s ease-in-out infinite;
        }
        
        .bazi-table {
            width: 100%;
            table-layout: fixed;
        }
        
        .bazi-header {
            font-family: 'Cinzel Decorative', cursive;
            font-size: 1em;
            color: #40e0d0;
            margin-bottom: 12px;
            text-shadow: 0 0 10px rgba(64,224,208,0.5);
        }
        
        .stem {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.2em;
            color: #e8e8f0;
            line-height: 1.3;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        
        .branch {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.2em;
            color: #e8e8f0;
            line-height: 1.3;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        
        .day-master {
            color: #ffd700 !important;
            text-shadow: 
                0 0 15px rgba(255,215,0,0.7),
                0 0 30px rgba(168,85,247,0.5);
            animation: moon-glow 2s ease-in-out infinite;
        }
        
        .energy-val {
            font-size: 0.8em;
            color: #a855f7;
            font-family: 'Philosopher', serif;
            margin-top: 4px;
            text-shadow: 0 0 8px rgba(168,85,247,0.5);
        }
        
        @keyframes moon-glow {
            0%, 100% { filter: drop-shadow(0 0 8px rgba(232,232,240,0.5)); }
            50% { filter: drop-shadow(0 0 20px rgba(232,232,240,0.9)); }
        }
    </style>
    """

def get_quantum_theme_config():
    """Returns the Gypsy Mystic Theme configuration (Celestial, Magical)."""
    return {
        # --- Wood (Emerald Forest / Nature Spirit) ---
        "甲": {"color": "#22c55e", "icon": "🌲", "anim": "pulse-grow", "grad": "linear-gradient(135deg, #1a4d2e, #40e0d0)"}, 
        "乙": {"color": "#40e0d0", "icon": "🌿", "anim": "sway", "grad": "linear-gradient(to top, #0d5c4d, #40e0d0)"},
        "寅": {"color": "#10b981", "icon": "🐅", "anim": "pulse-grow", "grad": "linear-gradient(to top, #064e3b, #34d399)"},
        "卯": {"color": "#6ee7b7", "icon": "🐇", "anim": "sway", "grad": "linear-gradient(120deg, #059669, #6ee7b7)"},

        # --- Fire (Candle Flame / Passion) ---
        "丙": {"color": "#ff9f43", "icon": "☀️", "anim": "spin-slow", "grad": "radial-gradient(circle, #ff9f43, #c21e56)"}, 
        "丁": {"color": "#c21e56", "icon": "🕯️", "anim": "flicker", "grad": "linear-gradient(to top, #c21e56, #ff6b6b)"},
        "巳": {"color": "#f97316", "icon": "🐍", "anim": "sway", "grad": "linear-gradient(to right, #ea580c, #fbbf24)"},
        "午": {"color": "#ef4444", "icon": "🐎", "anim": "pulse-grow", "grad": "linear-gradient(to right, #dc2626, #f43f5e)"}, 

        # --- Earth (Crystal Cave / Sacred Ground) ---
        "戊": {"color": "#a855f7", "icon": "🏔️", "anim": "none", "grad": "linear-gradient(to top, #581c87, #a855f7)"}, 
        "己": {"color": "#c084fc", "icon": "🔮", "anim": "none", "grad": "linear-gradient(to top, #6b21a8, #d8b4fe)"},
        "辰": {"color": "#ffd700", "icon": "🐲", "anim": "sway", "grad": "linear-gradient(to top, #b8860b, #ffd700)"}, 
        "戌": {"color": "#a78bfa", "icon": "🌋", "anim": "none", "grad": "linear-gradient(to right, #2d1b4e, #7c3aed)"}, 
        "丑": {"color": "#facc15", "icon": "🐂", "anim": "none", "grad": "linear-gradient(to top, #ca8a04, #fde047)"}, 
        "未": {"color": "#fb923c", "icon": "🐑", "anim": "none", "grad": "linear-gradient(120deg, #ea580c, #fbbf24)"}, 

        # --- Metal (Silver Moon / Precious) ---
        "庚": {"color": "#e8e8f0", "icon": "⚔️", "anim": "none", "grad": "linear-gradient(to top, #94a3b8, #e8e8f0)"}, 
        "辛": {"color": "#ffd700", "icon": "💎", "anim": "flicker", "grad": "linear-gradient(135deg, #b8860b, #ffd700, #fff8dc)"},
        "申": {"color": "#cbd5e1", "icon": "🐵", "anim": "sway", "grad": "linear-gradient(to top, #475569, #94a3b8)"}, 
        "酉": {"color": "#f1f5f9", "icon": "🐓", "anim": "none", "grad": "linear-gradient(to top, #94a3b8, #f8fafc)"}, 

        # --- Water (Mystic Ocean / Deep Secrets) ---
        "壬": {"color": "#40e0d0", "icon": "🌊", "anim": "wave", "grad": "linear-gradient(to top, #0d5c4d, #40e0d0)"}, 
        "癸": {"color": "#a855f7", "icon": "☁️", "anim": "sway", "grad": "linear-gradient(to top, #581c87, #c084fc)"}, 
        "子": {"color": "#3b82f6", "icon": "🐀", "anim": "sway", "grad": "linear-gradient(15deg, #1e3a8a, #60a5fa)"}, 
        "亥": {"color": "#8b5cf6", "icon": "🐖", "anim": "sway", "grad": "linear-gradient(to top, #4c1d95, #a78bfa)"}, 
    }

def get_theme(char):
    """Retrieve theme for a given Bazi character."""
    theme = get_quantum_theme_config()
    return theme.get(char, {"color": "#FFF", "icon": "❓", "anim": "none", "grad": "none"})

def get_nature_color(char):
    """Retrieve nature color for a given Bazi character."""
    theme = get_theme(char)
    return theme["color"]
