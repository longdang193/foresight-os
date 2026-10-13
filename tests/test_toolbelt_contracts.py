from foresight_os.runtime.capabilities import (
    CapabilityDecision,
    CapabilityResolver,
    DEFAULT_CAPABILITIES,
)


def test_semantic_registry_contains_the_full_toolbelt():
    assert set(DEFAULT_CAPABILITIES) >= {
        "web_search",
        "page_retrieval",
        "web_crawl",
        "technology_signals",
        "market_signals",
        "macro_signals",
        "document_read",
        "spreadsheet_read",
        "data_analysis",
        "calculation",
        "graph_context",
        "domain_validation",
        "internal_knowledge",
        "artifact_generation",
    }


def test_unavailable_capabilities_are_truthful_and_lazy():
    resolution = CapabilityResolver().resolve(("document_read", "internal_knowledge", "artifact_generation"))

    assert all(not item.available for item in resolution.values())
    assert all(item.decision == CapabilityDecision.UNSUPPORTED for item in resolution.values())
    assert all("adapter is not activated" in item.reason for item in resolution.values())
