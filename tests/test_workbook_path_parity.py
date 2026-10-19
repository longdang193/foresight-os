import asyncio
import json
from pathlib import Path

from foresight_os.analysis.supplier_resilience import (
    analyze_supplier_resilience,
    run_supplier_resilience_workflow,
)
from foresight_os.analysis.workbook_engine import DomainAnalysis, WorkbookAnalysisEngine
from foresight_os.analysis.workbook_inputs import resolve_workbook_contract
from foresight_os.cli import main
from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.workflow import run_recipe_async


FIXTURE = Path("tests/fixtures/exercise/02_Supplier_Resilience.xlsx")


def test_materialize_scope_false_preserves_domain_rows_but_keeps_contract_identity(tmp_path):
    source = tmp_path / "supplier.xlsx"
    source.write_bytes(FIXTURE.read_bytes())
    contract = resolve_workbook_contract(
        "supplier_resilience",
        {"domain": "supplier_resilience", "entity_scope": ["DOES_NOT_EXIST"]},
    )

    result = WorkbookAnalysisEngine().run(
        source,
        contract,
        lambda material, normalized: DomainAnalysis(
            result=(len(material.table("Supplier_Master").rows), normalized.fingerprint),
        ),
        materialize_scope=False,
    )

    assert result.status == "completed"
    assert result.domain_result is not None
    assert result.domain_result.result[0] > 0
    assert result.domain_result.result[1] == contract.fingerprint


def test_cross_brief_workbook_contracts_keep_scope_and_identity_distinct(tmp_path):
    source = tmp_path / "supplier.xlsx"
    source.write_bytes(FIXTURE.read_bytes())
    engine = WorkbookAnalysisEngine()
    briefs = (
        resolve_workbook_contract("supplier_resilience", {"entity_scope": ["Cetus Electronics"], "scenarios": ["Short outage"]}),
        resolve_workbook_contract("supplier_resilience", {"entity_scope": ["Hansa Controls"], "scenarios": ["Short outage"]}),
        resolve_workbook_contract("supplier_resilience", {"stage_id": "supplier-stage", "entity_scope": ["Cetus Electronics"]}),
        resolve_workbook_contract("supplier_resilience", {"stage_id": "defaults"}),
    )

    results = [
        engine.run(
            source,
            contract,
            lambda material, normalized: DomainAnalysis(
                result=(len(material.table("Supplier_Master").rows), normalized.fingerprint),
            ),
            materialize_scope=True,
        )
        for contract in briefs
    ]

    assert all(result.status == "completed" for result in results)
    assert [result.domain_result.result[0] for result in results] == [3, 3, 3, 21]
    assert len({result.domain_result.result[1] for result in results}) == 4
    assert briefs[2].fingerprint != briefs[0].fingerprint
    assert briefs[3].required_tables == briefs[0].required_tables


def test_direct_workflow_and_approved_runtime_share_supplier_analysis_identity(tmp_path):
    source = tmp_path / "supplier.xlsx"
    source.write_bytes(FIXTURE.read_bytes())
    contract = resolve_workbook_contract("supplier_resilience", None)

    direct = analyze_supplier_resilience(source)
    workflow = run_supplier_resilience_workflow(
        AnalysisStore(tmp_path / "workflow"),
        source,
        human_decision="ACCEPT",
    )
    assert workflow.status == "accepted"
    assert workflow.supplier is not None
    assert workflow.supplier.source_sha256 == direct.source_sha256
    assert workflow.supplier.contract_fingerprint == direct.contract_fingerprint == contract.fingerprint
    assert workflow.analysis is not None
    assert len(workflow.analysis.calculations) == len(direct.state.calculations)

    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage(
        "supplier",
        ExecutionPattern.DIRECT,
        (),
        "supplier workbook",
        "typed-result",
        {},
        analysis_domains=("supplier_resilience",),
        executor_kind="deterministic_local",
    )
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )
    runtime = asyncio.run(
        run_recipe_async(
            recipe,
            "supplier workbook",
            object(),
            run_context={
                "workbook_source": source,
                "analysis_contracts": {"supplier_resilience": contract.to_dict()},
            },
        )
    )
    runtime_result = runtime.outputs[0]
    assert runtime_result.source_sha256 == direct.source_sha256
    assert runtime_result.contract_fingerprint == direct.contract_fingerprint
    assert len(runtime_result.state.calculations) == len(direct.state.calculations)


def test_cli_dispatches_the_same_workflow_and_reports_settlement(tmp_path, capsys):
    source = tmp_path / "supplier.xlsx"
    source.write_bytes(FIXTURE.read_bytes())

    assert main([
        "analyze",
        "--workbook",
        str(source),
        "--work-dir",
        str(tmp_path / "cli"),
        "--domain",
        "supplier_resilience",
        "--accept",
    ]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"accepted": True, "status": "accepted", "artifact_status": "accepted"}
