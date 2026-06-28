"""Tests for finding card enrichment models."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from audit_data_schema import (Finding, AnxietyDriver, IndustryBenchmark,
    DiscoveryQuestions, AlgoliaAngle, ValueMap, ObjectionHandler)

class TestFindingEnrichmentModels:
    def test_finding_accepts_full_enrichment(self):
        f = Finding(
            id="F01", title="Test", severity="critical",
            category="Semantic Search", tested_query="test",
            actual_behavior="zero results",
            pain_frame="Every campaign ends at a dead end.",
            anxiety_driver=AnxietyDriver(
                calculation="250M × 3.2% × 2.1% × MXN 1200",
                competitor_comparison="Leroy Merlin maps ofertas in real-time.",
                quantified_impact="MXN ~200M/year"
            ),
            industry_benchmark=IndustryBenchmark(
                metric_name="Promotional intent recovery",
                best_in_class="97%", current_score="0%", gap="97 points",
                source="https://baymard.com/research/product-search"
            ),
            discovery_questions=DiscoveryQuestions(
                situation="How does your team manage campaign keywords?",
                problem="What happens when customers search 'oferta'?",
                implication="What happens to campaign ROI?",
                need_payoff="What if promo keywords surfaced your active catalog?"
            ),
            algolia_angle=AlgoliaAngle(
                capability="Rules Engine",
                specifics="Map oferta → dynamic promotional index.",
                time_to_value="< 1 hour"
            ),
            value_map=ValueMap(
                gap="Zero promo results", capability="Rules Engine",
                outcome="Promo recovery", metric="+2.1% conversion"
            ),
            objection_handling=[ObjectionHandler(
                objection="We can configure WCS espots.",
                counter="WCS espots don't extend to search layer.",
                evidence_ref="screenshots/19-banners-oferta.png"
            )]
        )
        assert f.pain_frame == "Every campaign ends at a dead end."
        assert f.anxiety_driver.quantified_impact == "MXN ~200M/year"
        assert f.industry_benchmark.source == "https://baymard.com/research/product-search"
        assert len(f.objection_handling) == 1

    def test_finding_valid_without_enrichment(self):
        f = Finding(
            id="F01", title="Test", severity="critical",
            category="Semantic Search", tested_query="test",
            actual_behavior="zero results"
        )
        assert f.pain_frame is None
        assert f.objection_handling == []

    def test_industry_benchmark_requires_source(self):
        with pytest.raises(Exception):
            IndustryBenchmark(
                metric_name="Recovery rate", best_in_class="97%",
                current_score="0%", gap="97 points", source=""
            )

    def test_anxiety_driver_requires_quantified_impact(self):
        with pytest.raises(Exception):
            AnxietyDriver(
                calculation="...", competitor_comparison="...",
                quantified_impact=""
            )

import json, subprocess, copy

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..')
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'valid_audit_data.json')
VALIDATOR = os.path.join(SCRIPTS_DIR, 'validate-json-schema.py')

def run_validator(data: dict, tmp_dir: str) -> tuple[int, str]:
    slug = 'testco'
    json_path = os.path.join(tmp_dir, f'{slug}-audit-data.json')
    with open(json_path, 'w') as f:
        json.dump(data, f)
    result = subprocess.run(
        ['python3', VALIDATOR, slug],
        capture_output=True, text=True, cwd=tmp_dir
    )
    return result.returncode, result.stdout + result.stderr

class TestFindingEnrichmentValidator:
    @pytest.fixture
    def base(self):
        with open(FIXTURE_PATH) as f:
            return json.load(f)

    def test_industry_benchmark_empty_source_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['findings'][0]['industry_benchmark'] = {
            "metric_name": "Recovery rate", "best_in_class": "97%",
            "current_score": "0%", "gap": "97 points", "source": ""
        }
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"Empty benchmark source must exit 1. Got {rc}.\n{out}"

    def test_valid_enriched_finding_exits_0(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['findings'][0]['pain_frame'] = "Every campaign ends at a dead end."
        data['findings'][0]['industry_benchmark'] = {
            "metric_name": "Promotional intent recovery", "best_in_class": "97%",
            "current_score": "0%", "gap": "97 points",
            "source": "https://baymard.com/research/product-search"
        }
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 0, f"Valid enriched finding must exit 0. Got {rc}.\n{out}"
