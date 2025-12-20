import sys
import os
sys.path.append(os.getcwd())
try:
    from bazi_predict.core.alchemy import AlchemyEngine
    print("AlchemyEngine imported successfully.")
    
    # Mock data
    chart = {
        'year': {'stem': '甲', 'branch': '子'},
        'month': {'stem': '己', 'branch': '丑'}, # Jia-Ji combine + Earth Month -> Transform
        'day': {'stem': '丙', 'branch': '寅'},
        'hour': {'stem': '辛', 'branch': '卯'}
    }
    
    engine = AlchemyEngine(chart)
    reactions = engine.run_reactions()
    print("Reactions detected:", reactions)
    
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
