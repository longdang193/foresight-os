from pathlib import Path

from foresight_os.graph import build_graph, get_context, get_impacted_records, trace_provenance
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_graph_rebuild_and_queries_are_deterministic(tmp_path: Path):
    run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)
    state = AnalysisStore(tmp_path / "case-001").load_analysis()

    first = build_graph(state)
    second = build_graph(state)
    assert list(first.nodes) == list(second.nodes)
    assert list(first.edges(keys=True)) == list(second.edges(keys=True))

    recommendation = state.recommendations[0].id
    assert trace_provenance(first, recommendation)
    assert get_context(first, recommendation)["evidence"]
    changed = next(item.id for item in state.evidence if "capacity_index-2030" in item.id)
    assert recommendation in get_impacted_records(first, changed)
