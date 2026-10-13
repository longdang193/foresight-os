from foresight_os.runtime.capabilities import (
    CapabilityDecision,
    CapabilityResolver,
    DEFAULT_CAPABILITIES,
    register_artifact_generation_adapter,
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
        "powerbi_project_read",
        "internal_knowledge",
        "artifact_generation",
    }


def test_unavailable_capabilities_are_truthful_and_lazy():
    resolution = CapabilityResolver().resolve(("document_read", "internal_knowledge", "artifact_generation"))

    assert all(not item.available for item in resolution.values())
    assert all(item.decision == CapabilityDecision.UNSUPPORTED for item in resolution.values())
    assert all("adapter is not activated" in item.reason for item in resolution.values())


def test_artifact_generation_activates_only_with_adapter_and_human_approval():
    context = {"human_approved": True}
    adapter = object()
    register_artifact_generation_adapter(context, adapter, fingerprint="canva-v1")

    resolution = CapabilityResolver().resolve(("artifact_generation",), context)["artifact_generation"]

    assert resolution.available
    assert resolution.tool is adapter
