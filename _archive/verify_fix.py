import sys
import os
sys.path.append(os.getcwd())
try:
    from bazi_predict.core.calculator import BaziCalculator
    calc = BaziCalculator(2024, 1, 1, 12, 0)
    chart = calc.get_chart()
    print("Chart calculated successfully:")
    print(chart)
except  Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
