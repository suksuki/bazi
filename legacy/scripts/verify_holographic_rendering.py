import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from ui.pages.document_management import render_holographic_markdown

class MockController:
    def get_documents_by_category(self, category=None):
        class Doc:
            def __init__(self, name): self.filename = name
        return [Doc("FDS_MODELING_SPEC_v3.0.md"), Doc("TEST_DOC.md")]

def test_rendering():
    controller = MockController()
    print("🧪 Starting Holographic Rendering V3.5 Verification...")

    # Case 1: LaTeX Protection
    content_latex = "Formulas: $$N_{hit} / N_{total}$$ and $x$."
    rendered = render_holographic_markdown(controller, content_latex, "FDS_MODELING_SPEC_v3.0.md")
    if "href=" in rendered and ("N_{hit}" in rendered or "N_total" in rendered):
        print("❌ LaTeX Protection Failed: Link injected inside formula.")
    else:
        print("✅ LaTeX Protection Passed.")

    # Case 2: Config Link Transformation
    content_cfg = "Adjust @config.gating.weak_self_limit now."
    rendered = render_holographic_markdown(controller, content_cfg, "FDS_MODELING_SPEC_v3.0.md")
    if 'class="config-ref-link"' in rendered and 'configPath: "gating.weak_self_limit"' in rendered:
        print("✅ Config Link Transformation Passed.")
    else:
        # Debugging output if it fails
        if 'class="config-ref-link"' in rendered:
            print(f"❌ Config Link Transformation Failed (Sub-string match error).")
            # print(f"DEBUG: {rendered}")
        else:
            print("❌ Config Link Transformation Failed (No link found).")

    # Case 3: Backtick Content Preservation
    content_backtick = "Use `category: WEALTH` in metadata."
    rendered = render_holographic_markdown(controller, content_backtick, "FDS_MODELING_SPEC_v3.0.md")
    if "`category: WEALTH`" in rendered:
        print("✅ Regular Backtick Content Preserved.")
    else:
        print("❌ Backtick Content Lost or Corrupted.")

    # Case 4: Backtick Strip for Technical Identifiers
    content_cfg_tick = "See `@config.gating.weak_self_limit`."
    rendered = render_holographic_markdown(controller, content_cfg_tick, "FDS_MODELING_SPEC_v3.0.md")
    if "`" in rendered and "config-ref-link" in rendered:
        print("❌ Backtick Strip Failed: Backticks remain around HTML link.")
    elif "config-ref-link" in rendered:
        print("✅ Backtick Strip Passed.")
    else:
        print("❌ Config Link Matching Failed.")

    # Case 5: Placeholder Index Collision (1 vs 10)
    # Generate > 10 masked items
    content_many = " ".join([f"`item_{i}`" for i in range(15)])
    rendered = render_holographic_markdown(controller, content_many, "FDS_MODELING_SPEC_v3.0.md")
    if all(f"`item_{i}`" in rendered for i in range(15)):
        print("✅ Placeholder Collision Fix Verified (V3.5 Inverse Replacement).")
    else:
        print("❌ Placeholder Collision Detected: Some backtick content is missing.")

    print("\n🎉 Rendering Verification Complete.")

if __name__ == "__main__":
    test_rendering()
