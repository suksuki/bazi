
"""
ui/components/styles.py
-----------------------
CSS styles for the Quantum UI.
"""

def get_glassmorphism_css():
    """Returns the main card styles."""
    return """
    <style>
    /* 1. Reset Global Background to Default */
    /* No .stApp override */

    /* 2. Card Container (Deep Space Dark) */
    .narrative-card {
        position: relative;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        background: #1e293b;
    }
    .narrative-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.5);
        border-color: #475569;
    }

    /* 3. Card Types / Themes (Dark Mode Adapted) */
    /* Mountain Alliance */
    .card-mountain {
        background: linear-gradient(to bottom right, #451a03, #1e293b);
        border-top: 3px solid #f59e0b;
    }
    .icon-mountain {
        font-size: 32px;
        color: #f59e0b;
    }

    /* Penalty Cap */
    .card-shield {
        background: linear-gradient(to bottom right, #0c4a6e, #1e293b);
        border-top: 3px solid #38bdf8;
    }
    .icon-shield {
        font-size: 32px;
        color: #38bdf8;
    }

    /* Mediation Flow */
    .card-flow {
        background: linear-gradient(to bottom right, #064e3b, #1e293b);
        border-top: 3px solid #34d399;
    }
    .icon-flow {
        font-size: 32px;
        color: #34d399;
    }

    /* Danger / Pressure */
    .card-danger {
        background: linear-gradient(to bottom right, #7f1d1d, #1e293b);
        border-top: 3px solid #f87171;
    }

    /* 4. Typography (Light Text) */
    .card-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 4px;
        color: #f1f5f9;
    }
    .card-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #94a3b8;
        margin-bottom: 12px;
    }
    .card-impact {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        padding: 4px 8px;
        border-radius: 4px;
        background: #334155;
        display: inline-block;
        color: #e2e8f0;
        font-weight: 600;
    }
    </style>
    """

def get_animation_css():
    """Returns animation and token styles."""
    return """
    <style>
        /* --- Animations --- */
        @keyframes sway { 0% { transform: rotate(0deg); } 25% { transform: rotate(5deg); } 75% { transform: rotate(-5deg); } 100% { transform: rotate(0deg); } }
        @keyframes pulse-grow { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        @keyframes flicker { 0% { opacity: 1; } 50% { opacity: 0.8; transform: scale(0.98); } 100% { opacity: 1; } }
        @keyframes spin-slow { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes wave { 0% { transform: translateY(0); } 50% { transform: translateY(-3px); } 100% { transform: translateY(0); } }
        @keyframes drift { 0% { transform: translateX(0); opacity: 0.8;} 50% { transform: translateX(5px); opacity: 1;} 100% { transform: translateX(0); opacity: 0.8;} }
        @keyframes sparkle { 0% { filter: brightness(100%); } 50% { filter: brightness(130%); } 100% { filter: brightness(100%); } }
        @keyframes flash { 0% { text-shadow: 0 0 5px #FFF; } 50% { text-shadow: 0 0 20px #FFF; } 100% { text-shadow: 0 0 5px #FFF; } }
        
        /* --- Card Styles --- */
        .pillar-card {
            background: #1e293b;
            border-radius: 15px;
            padding: 10px;
            text-align: center;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .pillar-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0,0,0,0.5);
            border-color: #475569;
        }
        .pillar-title {
            font-size: 0.75em;
            color: #94a3b8;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        /* --- Quantum Token (The Character) --- */
        .quantum-token {
            display: inline-block;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            margin: 5px auto;
            position: relative;
            
            /* Center Content */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5), 0 0 10px rgba(0,0,0,0.5);
            border: 2px solid rgba(255,255,255,0.1);
        }
        
        .token-char {
            font-size: 1.8em;
            font-weight: bold;
            color: #FFF;
            text-shadow: 0 2px 4px rgba(0,0,0,0.8);
            line-height: 1;
            z-index: 2;
        }
        
        .token-icon {
            font-size: 0.8em;
            position: absolute;
            top: 5px;
            right: 5px;
            filter: drop-shadow(0 0 2px rgba(0,0,0,0.8));
            z-index: 3;
        }
        
        .hidden-stems {
            font-size: 0.7em;
            color: #666;
            margin-top: 8px;
            font-family: monospace;
        }
        
        .hidden-container {
            display: flex;
            justify-content: center;
            gap: 6px; /* Space between quark particles */
            margin-top: 12px;
        }
        
        .hidden-token {
            width: 28px;
            height: 28px;
            border-radius: 50%; /* Perfect circle */
            font-size: 0.9em;
            font-weight: bold;
            color: #FFF;
            
            /* Centering */
            display: flex;
            align-items: center;
            justify-content: center;
            
            /* Quantum styling */
            box-shadow: 0 2px 4px rgba(0,0,0,0.6);
            border: 1px solid rgba(255,255,255,0.3);
            text-shadow: 0 1px 2px rgba(0,0,0,0.8);
            
            cursor: help;
            transition: transform 0.2s;
        }
        
        .hidden-token:hover {
            transform: scale(1.2) rotate(15deg);
            z-index: 10;
        }
        
        .dm-glow {
            box-shadow: 0 0 15px #FF4500, inset 0 0 10px #FF4500 !important;
            border: 2px solid #FF4500 !important;
        }
    </style>
    """

def get_bazi_table_css():
    """Returns the CSS for the Bazi Table."""
    return """
    <style>
        .bazi-box {
            background-color: #1e293b;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-family: 'Courier New', Courier, monospace;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #334155;
        }
        .bazi-table {
            width: 100%;
            table-layout: fixed;
            border-collapse: separate;
            border-spacing: 5px 0;
        }
        .bazi-header {
            font-size: 0.85em;
            color: #94a3b8;
            margin-bottom: 8px;
            display: inline-block;
            white-space: nowrap;
        }
        /* Title Animations */
        .h-anim-year { animation: wave 3s ease-in-out infinite; color: #4ade80; }
        .h-anim-month { animation: drift 5s ease-in-out infinite; color: #38bdf8; }
        .h-anim-day { animation: pulse-grow 2.5s ease-in-out infinite; color: #fbbf24; font-weight: bold; }
        .h-anim-hour { animation: sway 4s ease-in-out infinite; color: #c084fc; }
        .h-anim-dayun { animation: wave 6s ease-in-out infinite alternate; color: #22d3ee; opacity: 0.9; }
        .h-anim-liunian { animation: flash 3s ease-in-out infinite; color: #f472b6; }
        /* Column Highlight for Day Master */
        .col-day {
            background: #334155;
            border-radius: 8px;
        }
        
        .stem {
            font-size: 1.8em;
            font-weight: bold;
            color: #f1f5f9;
            line-height: 1.1;
        }
        .branch {
            font-size: 1.8em;
            font-weight: bold;
            color: #e2e8f0;
            line-height: 1.1;
        }
        .day-master {
            text-decoration: underline;
            text-decoration-color: #f97316;
            text-decoration-thickness: 3px;
        }
        .energy-val {
            font-size: 0.75em;
            color: #15803d; /* Safe Dark Green */
            font-family: 'Verdana', sans-serif;
            font-weight: 900;
            margin-top: -2px;
            margin-bottom: 2px;
        }
        .energy-val-low {
             font-size: 0.75em;
             color: #cbd5e1; /* Silver */
             font-family: 'Verdana', sans-serif;
             font-weight: bold;
             margin-top: -2px;
             margin-bottom: 2px;
        }
        .int-container {
            min-height: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        /* Dynamic Columns distinct style */
        .dynamic-col {
            background: #0f172a;
            border-radius: 8px;
        }
    </style>
    """

def get_quantum_theme_config():
    """Returns the Quantum Theme configuration."""
    return {
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
    """Retrieve theme for a given Bazi character."""
    theme = get_quantum_theme_config()
    return theme.get(char, {"color": "#FFF", "icon": "❓", "anim": "none", "grad": "none"})

def get_nature_color(char):
    """Retrieve nature color for a given Bazi character."""
    return get_theme(char)["color"]
