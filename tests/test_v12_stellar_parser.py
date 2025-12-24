
import random
import sys
import os

# Add parent directory to path to import core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.utils import Stellar_Comedy_Parser

def test_stellar_parser_sai_high():
    print("Testing SAI high...")
    result = Stellar_Comedy_Parser.translate(sai=2.5, entropy=1.0)
    found = False
    for phrase in Stellar_Comedy_Parser.DICTIONARY["SAI"]:
        if phrase in result:
            found = True
            break
    assert found
    print("SAI high passed.")

def test_stellar_parser_entropy_high():
    print("Testing Entropy high...")
    result = Stellar_Comedy_Parser.translate(sai=1.0, entropy=2.0)
    found = False
    for phrase in Stellar_Comedy_Parser.DICTIONARY["SINGULARITY"]:
        if phrase in result:
            found = True
            break
    assert found
    print("Entropy high passed.")

def test_stellar_parser_ic_low():
    print("Testing IC low...")
    result = Stellar_Comedy_Parser.translate(sai=1.0, entropy=1.0, ic=0.1)
    found = False
    for phrase in Stellar_Comedy_Parser.DICTIONARY["SIGNAL_LOSS"]:
        if phrase in result:
            found = True
            break
    assert found
    print("IC low passed.")

def test_stellar_parser_fallback():
    print("Testing fallback...")
    result = Stellar_Comedy_Parser.translate(sai=1.0, entropy=1.0, ic=0.5)
    assert "萤火虫" in result
    print("Fallback passed.")

if __name__ == "__main__":
    try:
        test_stellar_parser_sai_high()
        test_stellar_parser_entropy_high()
        test_stellar_parser_ic_low()
        test_stellar_parser_fallback()
        print("\nAll tests passed successfully!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
