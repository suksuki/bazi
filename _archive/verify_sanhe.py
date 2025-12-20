import sys
import os
sys.path.append(os.getcwd())
from bazi_predict.core.calculator import BaziCalculator
from bazi_predict.core.alchemy import AlchemyEngine

# User Case: 1977-05-08 17:00
# Year: Ding Si (Snake)
# Month: ? (Python will calc)
# Day: ?
# Hour: You (Rooster)
# We expect to see 'Si', 'You', 'Chou' in the branches for it to be a full frame.
# Let's check what the chart actually is.
try:
    calc = BaziCalculator(1977, 5, 8, 17, 0)
    chart = calc.get_chart()
    print("Chart:", chart['year']['branch'], chart['month']['branch'], chart['day']['branch'], chart['hour']['branch'])
    
    engine = AlchemyEngine(chart)
    reactions = engine.run_reactions()
    print("Reactions:", reactions)
    
    # Check for San He Jin (Metal)
    found_metal = any(r['product'] == 'Jin' and "San He" in r['type'] for r in reactions)
    if found_metal:
        print("SUCCESS: Metal Bureau Detected.")
    else:
        print("PARTIAL/FAIL: Metal Bureau NOT detected (Maybe missing one leg? Need to verify chart branches)")

except Exception as e:
    print(e)
