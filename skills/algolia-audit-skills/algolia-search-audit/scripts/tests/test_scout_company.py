from unittest.mock import patch
import sys
import os
import importlib.util

# Add parent directory to path BEFORE importing
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import scout_company
import scout_company

# Import collect_company from collect-company.py (with hyphen)
spec = importlib.util.spec_from_file_location("collect_company", os.path.join(parent_dir, "collect-company.py"))
collect_company = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect_company)

def test_extract_linkedin_from_markdown():
    """Test: extract_social_links finds LinkedIn URL in scraped markdown"""
    md = "Follow us on [LinkedIn](https://www.linkedin.com/company/acme) and Twitter."
    result = scout_company.extract_social_links(md, [])
    assert result["linkedin_url"] == "https://www.linkedin.com/company/acme"

def test_extract_twitter_from_markdown():
    """Test: extract_social_links finds Twitter handle in markdown"""
    md = "Follow us @AcmeCorp on Twitter."
    result = scout_company.extract_social_links(md, [])
    assert result["twitter_handle"] == "@AcmeCorp"

def test_extract_linkedin_from_links():
    """Test: extract_social_links uses links list as fallback for LinkedIn"""
    links = ["https://www.linkedin.com/company/acme", "https://twitter.com/acme"]
    result = scout_company.extract_social_links("", links)
    assert result["linkedin_url"] == "https://www.linkedin.com/company/acme"

def test_extract_twitter_from_links():
    """Test: extract_social_links uses links list as fallback for Twitter"""
    links = ["https://www.linkedin.com/company/acme", "https://twitter.com/acme"]
    result = scout_company.extract_social_links("", links)
    assert result["twitter_handle"] == "@acme"

def test_extract_empty_returns_nulls():
    """Test: extract_social_links returns None for empty inputs"""
    result = scout_company.extract_social_links("", [])
    assert result["linkedin_url"] is None
    assert result["twitter_handle"] is None

@patch("scout_company.requests.get")
def test_scout_available_health_check(mock_get):
    """Test: scout_available checks health endpoint"""
    mock_response = type('Response', (), {'status_code': 200})()
    mock_get.return_value = mock_response
    result = scout_company.scout_available()
    assert result is True

@patch("scout_company.requests.get")
def test_scout_unavailable_connection_error(mock_get):
    """Test: scout_available handles connection errors gracefully"""
    mock_get.side_effect = Exception("Connection refused")
    result = scout_company.scout_available()
    assert result is False

@patch("scout_company.requests.post")
def test_scrape_with_scout_handles_errors(mock_post):
    """Test: scrape_with_scout handles connection errors gracefully"""
    mock_post.side_effect = ConnectionRefusedError("Scout not running")
    result = scout_company.scrape_with_scout("https://acme.com/about")
    assert result["success"] is False
    assert "error" in result
    assert result["markdown"] == ""
    assert result["links"] == []

# ── Tests for merge_scout_fields (Task 2) ────────────────────────────────────

def test_merge_scout_does_not_overwrite_existing():
	"""Test: merge_scout_fields preserves existing non-null values"""
	existing = {
		"linkedin_url": "https://linkedin.com/company/existing",
		"twitter_handle": "@existing",
		"website": None
	}
	scout = {
		"linkedin_url": "https://linkedin.com/company/scout",
		"twitter_handle": "@scout",
		"website": "https://www.acme.com"
	}
	result = collect_company.merge_scout_fields(existing, scout)
	# Existing non-null values preserved
	assert result["linkedin_url"] == "https://linkedin.com/company/existing"
	assert result["twitter_handle"] == "@existing"
	# Null values filled by Scout
	assert result["website"] == "https://www.acme.com"

def test_merge_scout_fills_null_fields():
	"""Test: merge_scout_fields fills all null fields from Scout"""
	existing = {
		"linkedin_url": None,
		"twitter_handle": None,
		"careers_url": None,
		"website": None
	}
	scout = {
		"linkedin_url": "https://linkedin.com/company/scout",
		"twitter_handle": "@scout",
		"careers_url": "https://acme.com/careers",
		"website": "https://acme.com"
	}
	result = collect_company.merge_scout_fields(existing, scout)
	assert result["linkedin_url"] == "https://linkedin.com/company/scout"
	assert result["twitter_handle"] == "@scout"
	assert result["careers_url"] == "https://acme.com/careers"
	assert result["website"] == "https://acme.com"
