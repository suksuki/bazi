
"""
ui/components/styles.py
-----------------------
CSS styles for the Mystic/Ancient UI.
"""

def get_glassmorphism_css():
    """Returns the main card styles (Mystic Theme)."""
    return """
    <style>
    /* 1. Reset Global Background to Default */
    /* No .stApp override */

    /* 2. Narrative Card (Ancient Text Fragment) */
    .narrative-card {
        position: relative;
        padding: 24px;
        border-radius: 4px; /* Sharper corners */
        border: 1px solid #444;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        margin-bottom: 20px;
        background: radial-gradient(circle at top left, #2b2b2b, #1a1a1a);
        border-left: 2px solid #888;
    }
    .narrative-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.6);
        border-color: #d4af37; /* Gold hover */
    }

    /* 3. Card Types / Themes */
    /* Mountain Alliance */
    .card-mountain {
        background: linear-gradient(to bottom right, #3e2723, #1a1a1a); /* Dark Brown */
        border-top: 2px solid #d4af37; /* Gold */
    }
    .icon-mountain {
        font-size: 32px;
        color: #d4af37;
    }

    /* Penalty Cap - Water Shield */
    .card-shield {
        background: linear-gradient(to bottom right, #001f3f, #1a1a1a); /* Navy */
        border-top: 2px solid #7FBCAC; /* Jade */
    }
    .icon-shield {
        font-size: 32px;
        color: #7FBCAC;
    }

    /* Mediation Flow - Wood */
    .card-flow {
        background: linear-gradient(to bottom right, #1b4d3e, #1a1a1a); /* Forest */
        border-top: 2px solid #4E6E5D;
    }
    .icon-flow {
        font-size: 32px;
        color: #4E6E5D;
    }

    /* Danger - Cinnabar */
    .card-danger {
        background: linear-gradient(to bottom right, #4a1c1c, #1a1a1a);
        border-top: 2px solid #aa3a3a;
    }

    /* 4. Typography (Serif) */
    .card-title {
        font-family: 'Ma Shan Zheng', cursive;
        font-weight: 400;
        font-size: 1.3rem;
        margin-bottom: 4px;
        color: #e0e0e0;
        letter-spacing: 1px;
    }
    .card-subtitle {
        font-family: 'Noto Serif SC', serif;
        font-size: 0.95rem;
        color: #aaa;
        margin-bottom: 12px;
    }
    .card-impact {
        font-family: 'Noto Serif SC', serif;
        font-size: 0.85rem;
        padding: 4px 8px;
        border-radius: 2px;
        background: #333;
        display: inline-block;
        color: #d4af37;
        border: 1px solid #555;
    }
    </style>
    """

def get_animation_css():
    """Returns animation and token styles (Mystic/Seal Style)."""
    return """
    <style>
        /* --- Animations (Subtle Qi Flow) --- */
        @keyframes sway { 0% { transform: rotate(0deg); } 50% { transform: rotate(2deg); } 100% { transform: rotate(0deg); } }
        @keyframes pulse-grow { 0% { transform: scale(1); opacity: 0.9; } 50% { transform: scale(1.02); opacity: 1; } 100% { transform: scale(1); opacity: 0.9; } }
        @keyframes flicker { 0% { opacity: 0.95; } 50% { opacity: 0.8; } 100% { opacity: 0.95; } }
        @keyframes spin-slow { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes wave { 0% { transform: translateY(0); } 50% { transform: translateY(-3px); } 100% { transform: translateY(0); } }
        
        /* --- Card Styles (Spirit Tablet / Wooden Block) --- */
        .pillar-card {
            background: #232323;
            border-radius: 6px;
            padding: 15px 10px;
            text-align: center;
            border: 1px solid #3a3a3a;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
            transition: all 0.3s ease;
            position: relative;
        }
        .pillar-card:hover {
            border-color: #d4af37;
            box-shadow: 0 0 15px rgba(212, 175, 55, 0.15);
            transform: translateY(-3px);
        }
        .pillar-title {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 1em;
            color: #888;
            margin-bottom: 12px;
            border-bottom: 1px solid #444;
            padding-bottom: 5px;
        }
        
        /* --- Quantum Token (The Seal/Stamp) --- */
        .quantum-token {
            display: inline-block;
            width: 70px;
            height: 70px;
            border-radius: 50%; /* Start circular */
            margin: 5px auto;
            position: relative;
            
            /* Center Content */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            
            /* Seal Style */
            background-color: #1a1a1a;
            border: 2px solid rgba(255,255,255,0.2);
            box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        }
        
        .token-char {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.2em;
            color: #FFF;
            text-shadow: 0 2px 4px rgba(0,0,0,0.9);
            z-index: 2;
        }
        
        .token-icon {
            font-size: 0.7em;
            position: absolute;
            top: 2px;
            right: 0;
            opacity: 0.8;
            z-index: 3;
        }
        
        /* Hidden Stems (Small Seals) */
        .hidden-container {
            display: flex;
            justify-content: center;
            gap: 8px; 
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px dashed #333;
        }
        
        .hidden-token {
            width: 24px;
            height: 24px;
            border-radius: 4px; /* Square seals for hidden */
            font-family: 'Noto Serif SC', serif;
            font-size: 0.8em;
            color: #FFF;
            
            display: flex;
            align-items: center;
            justify-content: center;
            
            box-shadow: 0 1px 3px rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.2);
            cursor: help;
        }
        
        .dm-glow {
            border-color: #d4af37 !important;
            box-shadow: 0 0 15px rgba(212, 175, 55, 0.3) !important;
        }
    </style>
    """

def get_bazi_table_css():
    """Returns the CSS for the Bazi Table (Scroll Style)."""
    return """
    <style>
        .bazi-box {
            background-color: #232323;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            font-family: 'Noto Serif SC', serif;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
            border: 1px solid #444;
        }
        .bazi-table {
            width: 100%;
            table-layout: fixed;
        }
        .bazi-header {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 0.9em;
            color: #aaa;
            margin-bottom: 8px;
        }
        
        .stem {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.0em;
            color: #f0f0e8;
            line-height: 1.2;
        }
        .branch {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.0em;
            color: #dcdcdc;
            line-height: 1.2;
        }
        .day-master {
            color: #d4af37 !important; /* Gold */
            text-shadow: 0 0 5px rgba(212, 175, 55, 0.5);
        }
        .energy-val {
            font-size: 0.75em;
            color: #7FBCAC; /* Jade */
            font-family: serif;
            margin-top: 2px;
        }
    </style>
    """

def get_quantum_theme_config():
    """Returns the Ancient Theme configuration (Muted, Natural)."""
    return {
        # --- Wood (Jade / Forest) ---
        "甲": {"color": "#4E6E5D", "icon": "🌲", "anim": "pulse-grow", "grad": "linear-gradient(135deg, #1b3a2b, #4e6e5d)"}, 
        "乙": {"color": "#7FBCAC", "icon": "🌿", "anim": "sway", "grad": "linear-gradient(to top, #2e5c4d, #7fbcac)"},
        "寅": {"color": "#2E7D32", "icon": "🐅", "anim": "pulse-grow", "grad": "linear-gradient(to top, #1b5e20, #4caf50)"},
        "卯": {"color": "#66BB6A", "icon": "🐇", "anim": "sway", "grad": "linear-gradient(120deg, #2e7d32, #81c784)"},

        # --- Fire (Cinnabar / Torch) ---
        "丙": {"color": "#D84315", "icon": "☀️", "anim": "spin-slow", "grad": "radial-gradient(circle, #e64a19, #bf360c)"}, 
        "丁": {"color": "#FF7043", "icon": "🕯️", "anim": "flicker", "grad": "linear-gradient(to top, #d84315, #ff8a65)"},
        "巳": {"color": "#F4511E", "icon": "🐍", "anim": "sway", "grad": "linear-gradient(to right, #bf360c, #f4511e)"},
        "午": {"color": "#C62828", "icon": "🐎", "anim": "pulse-grow", "grad": "linear-gradient(to right, #b71c1c, #e53935)"}, 

        # --- Earth (Ochre / Clay) ---
        "戊": {"color": "#795548", "icon": "🏔️", "anim": "none", "grad": "linear-gradient(to top, #4e342e, #8d6e63)"}, 
        "己": {"color": "#A1887F", "icon": "🧱", "anim": "none", "grad": "linear-gradient(to top, #5d4037, #bcaaa4)"},
        "辰": {"color": "#558B2F", "icon": "🐲", "anim": "sway", "grad": "linear-gradient(to top, #33691e, #689f38)"}, 
        "戌": {"color": "#8D6E63", "icon": "🌋", "anim": "none", "grad": "linear-gradient(to right, #3e2723, #5d4037)"}, 
        "丑": {"color": "#FBC02D", "icon": "🐂", "anim": "none", "grad": "linear-gradient(to top, #f57f17, #fbc02d)"}, 
        "未": {"color": "#F9A825", "icon": "🐑", "anim": "none", "grad": "linear-gradient(120deg, #fbc02d, #ffeb3b)"}, 

        # --- Metal (Silver / Bronze) ---
        "庚": {"color": "#90A4AE", "icon": "⚔️", "anim": "none", "grad": "linear-gradient(to top, #546e7a, #90a4ae)"}, 
        "辛": {"color": "#d4af37", "icon": "💎", "anim": "flicker", "grad": "linear-gradient(135deg, #b78628, #f7ef8a)"}, # Gold for Yin Metal
        "申": {"color": "#78909C", "icon": "🐵", "anim": "sway", "grad": "linear-gradient(to top, #455a64, #78909c)"}, 
        "酉": {"color": "#B0BEC5", "icon": "🐓", "anim": "none", "grad": "linear-gradient(to top, #78909c, #cfd8dc)"}, 

        # --- Water (Ink / Deep Sea) ---
        "壬": {"color": "#0277BD", "icon": "🌊", "anim": "wave", "grad": "linear-gradient(to top, #01579b, #0288d1)"}, 
        "癸": {"color": "#4FC3F7", "icon": "☁️", "anim": "sway", "grad": "linear-gradient(to top, #0277bd, #4fc3f7)"}, 
        "子": {"color": "#0288D1", "icon": "🐀", "anim": "sway", "grad": "linear-gradient(15deg, #01579b, #039be5)"}, 
        "亥": {"color": "#039BE5", "icon": "🐖", "anim": "sway", "grad": "linear-gradient(to top, #006064, #0097a7)"}, 
    }

def get_theme(char):
    """Retrieve theme for a given Bazi character."""
    theme = get_quantum_theme_config()
    return theme.get(char, {"color": "#FFF", "icon": "❓", "anim": "none", "grad": "none"})

def get_nature_color(char):
    """Retrieve nature color for a given Bazi character."""
    theme = get_theme(char)
    return theme["color"]
