import importlib

import pytest

from foresight_os.analysis.workbook_registry import (
    WORKBOOK_DOMAINS,
    default_workbook_contract_for,
    get_workbook_analyzer,
    workbook_analyzer_fingerprint_for,
    workbook_analyzer_version_for,
    workbook_analyzer_map,
)


def test_registry_covers_all_supported_workbook_domains():
    assert set(WORKBOOK_DOMAINS) == {
        "portfolio_resilience",
        "supplier_resilience",
        "ev_capacity_investment",
        "technology_radar",
        "powerbi_strategic_portfolio",
    }
    assert {default_workbook_contract_for(domain).domain for domain in WORKBOOK_DOMAINS} == set(WORKBOOK_DOMAINS)


def test_registry_rejects_unknown_domains():
    with pytest.raises(ValueError, match="unsupported workbook analysis domain"):
        default_workbook_contract_for("unknown")
    with pytest.raises(ValueError, match="unsupported workbook analysis domain"):
        get_workbook_analyzer("unknown")


def test_registry_keeps_versions_and_fingerprints_stable():
    versions = {domain: workbook_analyzer_version_for(domain) for domain in WORKBOOK_DOMAINS}
    fingerprints = {domain: workbook_analyzer_fingerprint_for(domain) for domain in WORKBOOK_DOMAINS}

    assert all(version for version in versions.values())
    assert all(len(fingerprint) == 64 for fingerprint in fingerprints.values())
    assert fingerprints == {domain: workbook_analyzer_fingerprint_for(domain) for domain in WORKBOOK_DOMAINS}


def test_registry_analyzer_map_loads_callables_on_lookup():
    registry_module = importlib.import_module("foresight_os.analysis.workbook_registry")
    analyzers = workbook_analyzer_map()

    assert set(analyzers) == set(WORKBOOK_DOMAINS)
    assert all(module_name not in registry_module.__dict__ for module_name in ("portfolio_resilience", "supplier_resilience"))
    assert callable(analyzers.get("portfolio_resilience"))
