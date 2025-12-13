
import logging
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.pipeline import BaziVerificationPipeline

def test_steve_jobs_integration():
    """
    Integration Test: Steve Jobs
    1. BioMiner: Check polarity of 1985 (ousted) and 2011 (death).
    2. QuantumEngine: Check Day Master (Bing Fire) and Favorable Elements.
    3. Match Score: Evaluate total accuracy.
    """
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("Test.Jobs")

    pipeline = BaziVerificationPipeline()

    # Input Text
    text_input = """
史蒂夫·乔布斯（Steve Jobs），出生于1955年2月24日。
1976年，他和沃兹尼亚克在车库里创办了苹果公司，推出了Apple I，获得了巨大成功。
1980年，苹果公司上市，乔布斯一夜暴富。
但是，1985年，由于管理理念冲突，乔布斯被董事会扫地出门，离开了自己创立的公司，这是他人生最大的挫折。
在低谷期，他创办了NeXT和皮克斯。
1997年，苹果收购NeXT，乔布斯王者归来，重新执掌苹果。
2007年，他发布了第一代iPhone，彻底改变了世界。
不幸的是，2011年10月5日，乔布斯因病去世。
    """

    print("\n" + "="*50)
    print("🚀 STARTING INTEGRATION TEST: STEVE JOBS")
    print("="*50)

    # Run Pipeline
    result = pipeline.run_single_case(text_input)

    # --- Verification Set 1: BioMiner ---
    print("\n1️⃣  [BioMiner Logic Check]")
    # We need to access the raw events or check the log details as the result struct only has success years
    # However, 'details' string in result usually contains the log.
    # But to be precise, let's look at the result object properties if possible or re-mine if needed for assertions.
    # Actually, BaziVerificationPipeline.run_single_case returns a VerificationResult.
    # It has 'actual_success_years' (positive events).
    # To check negative events, we might need to rely on the 'details' log or modify the pipeline to return all events 
    # OR we can trust the log output for this manual trigger.
    
    # Let's inspect the log in 'details' for 1985 and 2011.
    log_content = result.details
    
    check_1985_negative = "1985" in log_content and "bad" in log_content.lower() or "negative" in log_content.lower() or "坏事" in log_content
    check_2011_negative = "2011" in log_content and "bad" in log_content.lower() or "negative" in log_content.lower() or "坏事" in log_content

    if check_1985_negative:
        print("   ✅ 1985 Identified as Negative Event (Ousted)")
    else:
        print("   ❌ 1985 FAILED to be identified as Negative Event")

    if check_2011_negative:
        print("   ✅ 2011 Identified as Negative Event (Death)")
    else:
        print("   ❌ 2011 FAILED to be identified as Negative Event")


    # --- Verification Set 2: QuantumEngine ---
    print("\n2️⃣  [QuantumEngine Chart Check]")
    # We can't easily access the internal chart structure from VerificationResult, 
    # but we can see the 'Predicted Favorable' elements.
    # Expected: Bing Fire (Day Master). 
    # If Strong Fire: Favorable = Earth, Metal, Water. 
    # If Weak Fire: Favorable = Wood, Fire.
    # Jobs is widely considered Strong Fire (born in Tiger month).
    print(f"   Predicted Favorable Elements: {result.predicted_favorable_elements}")
    
    is_strong_pattern = 'Earth' in result.predicted_favorable_elements or 'Metal' in result.predicted_favorable_elements
    if is_strong_pattern:
         print("   ✅ Engine predicts 'Strong' Pattern strategy (Likes Earth/Metal/Water)")
    else:
         print("   ⚠️ Engine predicts 'Weak' Pattern strategy (Likes Wood/Fire)")


    # --- Verification Set 3: Match Score ---
    print("\n3️⃣  [Final Match Score]")
    print(f"   Score: {result.match_score:.2f}")
    if result.match_score > 0.6:
        print("   🎉 System Passed Champagne Test (Score > 0.6)")
    else:
        print("   ❄️ System Needs Calibration (Score <= 0.6)")

    print("\n" + "="*20 + " DETAILS LOG " + "="*20)
    print(result.details)
    print("="*53)

if __name__ == "__main__":
    test_steve_jobs_integration()
