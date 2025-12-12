import pytest
import json
from unittest.mock import MagicMock, patch

from service.processor import ContentProcessor
from service.sanitizer import Sanitizer
from service.web_hunter import WebHunter
from service.extractor import CaseExtractor

# ==========================================
# 1. Sanitizer Tests
# ==========================================
def test_sanitizer_cleaning():
    raw_text = "  Hello   World \n\n Test "
    # Logic in code: re.sub(r'\s+', ' ', clean_text).strip()
    # This collapses newlines into space too.
    assert Sanitizer.clean_text(raw_text) == "Hello World Test"

def test_sanitizer_translation():
    # Test term mapping
    assert "甲" in Sanitizer.clean_text("Yang Wood")
    assert "七杀" in Sanitizer.clean_text("Seven Killings")
    # Rodden Rating logic is separate (map_quality), but cleaner might affect it if passed as text?
    # Actually sanitizer processes known terms. "AA" is not in TERM_MAP.
    # But clean_text should preserve it.
    assert "Rodden Rating AA" in Sanitizer.clean_text("Rodden Rating AA")

# ==========================================
# 2. Processor Tests (Classification)
# ==========================================
def test_processor_classification_case():
    processor = ContentProcessor()
    # Case text: Contains birth info + subject
    case_text = "此男命生于1980年，日主为甲木。"
    assert processor.classify_content(case_text) == "CASE"

def test_processor_classification_rule():
    processor = ContentProcessor()
    # Rule text: Theory only
    rule_text = "凡是伤官见官，为祸百端。这是经典口诀。"
    assert processor.classify_content(rule_text) == "RULE"

def test_processor_classification_noise():
    processor = ContentProcessor()
    assert processor.classify_content("Hello world") == "NOISE"

# ==========================================
# 3. WebHunter Tests (Targeted Strategy)
# ==========================================
@patch('service.web_hunter.requests.get')
def test_web_hunter_adb_parsing(mock_get):
    # Mock ADB HTML Response
    mock_html = """
    <html>
        <h1 class="firstHeading">Jobs, Steve</h1>
        <table class="infobox">
            <tr><td><a title="Rodden Rating AA">AA</a></td></tr>
            <tr><td>born on 24 February 1955</td></tr>
        </table>
        <div class="mw-parser-output">
            <h2>Biography</h2>
            <p>He was a founder of Apple.</p>
        </div>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_html
    mock_get.return_value = mock_resp

    hunter = WebHunter()
    
    with patch.object(hunter.processor, 'process_text') as mock_process:
        success = hunter._hunt_adb_page("http://mock-url")
        assert success is True
        
        # Verify what was sent to processor
        args, _ = mock_process.call_args
        sent_text = args[0]
        
        # Depending on beautifier or processing, might vary slightly.
        # But core data must exist.
        assert "Name】 Jobs, Steve" in sent_text
        # Rodden Rating might catch 'AA'
        assert "Rodden Rating】 AA" in sent_text
        assert "Birth Data】" in sent_text
        assert "founder of Apple" in sent_text

# ==========================================
# 4. Extractor Tests (LLM Interface)
# ==========================================
@patch('service.extractor.ollama.Client')
def test_extractor_valid_json(mock_client_class):
    # Mock LLM Response - Return clean JSON without code blocks
    mock_response = {
        'message': {
            'content': '{"profile": {"name": "Jobs", "gender": "M", "birth_year": 1955, "birth_month": 2, "birth_day": 24, "birth_hour": 12, "birth_minute": 0, "birth_city": "SF"}, "life_events": [], "quality_score": 85, "valid_for_validation": false}'
        }
    }
    
    # Mock ollama.Client to return mock_chat behavior
    mock_client_instance = MagicMock()
    mock_client_instance.chat = MagicMock(return_value=mock_response)
    mock_client_class.return_value = mock_client_instance

    extractor = CaseExtractor()
    result = extractor.extract("Some text")
    
    assert result is not None
    assert result['profile']['name'] == "Jobs"
    assert result['profile']['birth_year'] == 1955


@patch('service.extractor.ollama.Client')
def test_extractor_invalid_json_handling(mock_client_class):
    # Mock Broken JSON
    mock_response = {
        'message': {
            'content': 'Sure, here is the data: {name: "Jobs" ... (cut off)'
        }
    }
    
    # Mock ollama.Client to return broken JSON
    mock_client_instance = MagicMock()
    mock_client_instance.chat = MagicMock(return_value=mock_response)
    mock_client_class.return_value = mock_client_instance

    extractor = CaseExtractor()
    result = extractor.extract("Some text")
    
    # Should handle error gracefully and fallback to regex extraction
    # Regex extraction returns None if no valid data is found in "Some text"
    assert result is None

