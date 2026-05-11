import pytest, json, os, tempfile, sys
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from collect-social.py using importlib
import importlib.util
spec = importlib.util.spec_from_file_location("collect_social", os.path.join(os.path.dirname(os.path.dirname(__file__)), "collect-social.py"))
collect_social = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect_social)

# Guard 1: skip LinkedIn actor if linkedin_url is null
def test_skip_linkedin_actor_if_no_url():
    assert collect_social.should_run_actor(None, "linkedin") == False
    assert collect_social.should_run_actor("", "linkedin") == False
    assert collect_social.should_run_actor("https://www.linkedin.com/company/acme", "linkedin") == True

# Guard 1: skip Twitter actor if twitter_handle is null
def test_skip_twitter_actor_if_no_handle():
    assert collect_social.should_run_actor(None, "twitter") == False
    assert collect_social.should_run_actor("", "twitter") == False
    assert collect_social.should_run_actor("@AcmeCorp", "twitter") == True

# Guard 3: cache miss (no cache file) → should run
def test_cache_miss_returns_none():
    with tempfile.TemporaryDirectory() as d:
        result = collect_social.load_cache(d, "acme.com")
    assert result is None

# Guard 3: cache hit (fresh, < 30 days) → should skip
def test_cache_hit_fresh_returns_data():
    with tempfile.TemporaryDirectory() as d:
        collect_social.write_cache(d, "acme.com", li_count=0, tw_count=0)
        result = collect_social.load_cache(d, "acme.com")
    assert result is not None
    assert result["li_count"] == 0

# Guard 3: cache hit (stale, > 30 days) → should run again
def test_cache_hit_stale_returns_none():
    with tempfile.TemporaryDirectory() as d:
        # Write cache with old date
        cache_path = os.path.join(d, ".social-cache.json")
        old_date = (date.today() - timedelta(days=collect_social.CACHE_TTL_DAYS + 1)).isoformat()
        with open(cache_path, "w") as f:
            json.dump({"acme.com": {"date": old_date, "li_count": 0, "tw_count": 0}}, f)
        result = collect_social.load_cache(d, "acme.com")
    assert result is None
