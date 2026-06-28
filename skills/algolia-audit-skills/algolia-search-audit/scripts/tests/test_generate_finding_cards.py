"""Tests for generate-finding-cards.py"""
import pytest
import os
import sys
import importlib.util

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..')
SCRIPT_PATH = os.path.join(SCRIPTS_DIR, 'generate-finding-cards.py')
RESEARCH_DIR = os.path.expanduser(
    "~/AI-Development/Algolia Search Audit/HomeDepot-Mexico/research"
)


def load_script():
    spec = importlib.util.spec_from_file_location("gen_fc", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestGenerateFindingCards:
    def test_script_exists(self):
        assert os.path.exists(SCRIPT_PATH)

    def test_load_research_files_returns_dict(self):
        mod = load_script()
        research = mod.load_research_files(RESEARCH_DIR)
        # At minimum scoring_matrix and company_context must be present for HD Mexico
        assert isinstance(research, dict)
        assert len(research) > 0

    def test_build_synthesis_prompt_contains_finding_id(self):
        mod = load_script()
        finding = {
            "id": "F06",
            "title": "Content Commerce UX",
            "severity": "critical",
            "tested_query": "oferta",
            "actual_behavior": "zero results",
        }
        research = {"scoring_matrix": "F06: 3/10", "company_context": "HD Mexico"}
        prompt = mod.build_synthesis_prompt(finding, research)
        assert "F06" in prompt
        assert len(prompt) > 200

    def test_parse_enrichment_json_valid(self):
        mod = load_script()
        response = '''```json
{
  "pain_frame": "Every campaign ends at a dead end.",
  "anxiety_driver": {"calculation": "250M x 3.2%", "competitor_comparison": "Leroy Merlin uses Algolia", "quantified_impact": "MXN ~200M/year"},
  "industry_benchmark": {"metric_name": "Recovery", "best_in_class": "97%", "current_score": "0%", "gap": "97pts", "source": "https://baymard.com"},
  "discovery_questions": {"situation": "How do you manage campaign keywords?", "problem": "What happens when customers search oferta?", "implication": "What happens to ROI?", "need_payoff": "What if promo keywords worked?"},
  "algolia_angle": {"capability": "Rules Engine", "specifics": "Map oferta to promo index", "time_to_value": "1 hour"},
  "value_map": {"gap": "Zero promo results", "capability": "Rules Engine", "outcome": "Promo recovery", "metric": "+2.1%"},
  "objection_handling": [{"objection": "WCS espots handle this", "counter": "Espots don't extend to search layer", "evidence_ref": "screenshots/19.png"}]
}
```'''
        result = mod.parse_enrichment_json(response)
        assert result['pain_frame'] == "Every campaign ends at a dead end."
        assert result['anxiety_driver']['quantified_impact'] == "MXN ~200M/year"
        assert len(result['objection_handling']) == 1

    def test_parse_enrichment_json_raises_on_missing_key(self):
        mod = load_script()
        with pytest.raises(ValueError, match="anxiety_driver|missing"):
            mod.parse_enrichment_json('```json\n{"pain_frame": "test"}\n```')
