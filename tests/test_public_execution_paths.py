from pathlib import Path

from foresight_os.clients.first_client_adapter import LocalClient


def test_local_client_exposes_gate_backed_execute():
    assert "execute" in LocalClient.__dict__
    assert Path("src/foresight_os/runtime/execution_gate.py").exists()
