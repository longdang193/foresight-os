from foresight_os.runtime.capabilities import (
    CapabilityDecision,
    DEFERRED_CAPABILITIES,
    REQUIRED_CAPABILITIES,
)
from foresight_os.runtime.maf_probe import (
    checkpoint_round_trip,
    load_provider_settings,
    maf_package_available,
    probe_capabilities,
    vertical_slice_guardrail,
)
from foresight_os.runtime.workflow import run_sequential_steps
import pytest
import subprocess
import sys


def test_provider_settings_load_custom_provider_from_env_and_codex_config(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("CUSTOM_ROUTER_API_KEY=secret\n", encoding="utf-8")
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        'model_provider = "custom"\nmodel = "router-model"\n'
        '[model_providers.custom]\nbase_url = "http://127.0.0.1:9999/v1"\ncredential_env = "CUSTOM_ROUTER_API_KEY"\n',
        encoding="utf-8",
    )

    settings = load_provider_settings(env_file, config_file)

    assert settings.provider == "custom"
    assert settings.model == "router-model"
    assert settings.base_url == "http://127.0.0.1:9999/v1"
    assert settings.api_key == "secret"


def test_provider_settings_uses_inherited_environment_when_env_file_is_absent(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        'model_provider = "custom"\nmodel = "router-model"\n'
        '[model_providers.custom]\nbase_url = "http://127.0.0.1:9999/v1"\ncredential_env = "CUSTOM_ROUTER_API_KEY"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CUSTOM_ROUTER_API_KEY", "inherited-secret")

    settings = load_provider_settings(tmp_path / "missing.env", config_file)

    assert settings.api_key == "inherited-secret"


def test_probe_returns_one_decision_for_every_required_capability():
    results = {result.name: result for result in probe_capabilities()}

    assert set(REQUIRED_CAPABILITIES).issubset(results)
    assert all(result.decision in CapabilityDecision for result in results.values())
    if not maf_package_available():
        assert all(results[name].decision == CapabilityDecision.UNSUPPORTED for name in REQUIRED_CAPABILITIES)
    else:
        assert results["single_agent"].decision == CapabilityDecision.ADAPT_AT_BOUNDARY
        assert results["sequential_review"].decision == CapabilityDecision.USE_NATIVE
        assert results["checkpoint_restart"].decision == CapabilityDecision.USE_NATIVE


def test_provider_settings_selects_only_configured_credential(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER_API_KEY=wrong\nCUSTOM_ROUTER_API_KEY=right\n", encoding="utf-8")
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        'model_provider = "custom"\nmodel = "router-model"\n'
        '[model_providers.custom]\nbase_url = "http://127.0.0.1:9999/v1"\ncredential_env = "CUSTOM_ROUTER_API_KEY"\n',
        encoding="utf-8",
    )

    settings = load_provider_settings(env_file, config_file)

    assert settings.credential_env == "CUSTOM_ROUTER_API_KEY"
    assert settings.api_key == "right"


def test_provider_settings_rejects_missing_configured_credential(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER_API_KEY=wrong\n", encoding="utf-8")
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        'model_provider = "custom"\nmodel = "router-model"\n'
        '[model_providers.custom]\nbase_url = "http://127.0.0.1:9999/v1"\ncredential_env = "CUSTOM_ROUTER_API_KEY"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CUSTOM_ROUTER_API_KEY"):
        load_provider_settings(env_file, config_file)


def test_checkpoint_round_trip_uses_maf_storage():
    assert maf_package_available()
    assert checkpoint_round_trip()


def test_native_checkpoint_state_survives_a_fresh_process(tmp_path):
    storage = tmp_path / "checkpoints"
    write = """
import asyncio, sys
from agent_framework import FileCheckpointStorage, WorkflowCheckpoint
async def main(path):
    checkpoint = WorkflowCheckpoint('foresight', 'native-v1', state={'completed_stages': ['stage-1']})
    checkpoint_id = await FileCheckpointStorage(path).save(checkpoint)
    print(checkpoint_id)
asyncio.run(main(sys.argv[1]))
"""
    checkpoint_id = subprocess.check_output([sys.executable, "-c", write, str(storage)], text=True).strip()
    read = """
import asyncio, sys
from agent_framework import FileCheckpointStorage
async def main(path, checkpoint_id):
    checkpoint = await FileCheckpointStorage(path).load(checkpoint_id)
    assert checkpoint.state == {'completed_stages': ['stage-1']}
asyncio.run(main(sys.argv[1], sys.argv[2]))
"""
    subprocess.run([sys.executable, "-c", read, str(storage), checkpoint_id], check=True)


def test_group_chat_is_native_and_magentic_is_deferred():
    results = {result.name: result for result in probe_capabilities()}

    assert results["pattern_group_chat"].decision == CapabilityDecision.USE_NATIVE
    assert all(results[name].decision == CapabilityDecision.DEFER for name in DEFERRED_CAPABILITIES)


def test_vertical_slice_guardrail_is_explicit():
    guardrail = vertical_slice_guardrail()

    assert guardrail.max_agent_steps == 5
    assert guardrail.max_correction_rounds == 1
    assert guardrail.max_total_agent_calls == 3
    assert "no accepted recommendation" in guardrail.exhaustion_outcome


def test_sequential_review_uses_native_workflow_builder():
    assert run_sequential_steps(["analyst", "reviewer"])["completed_stages"] == ["analyst", "reviewer"]
