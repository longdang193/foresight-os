from pathlib import Path

import pytest

from evaluation.participant_scope import ParticipantScope


def test_participant_scope_allows_case_files_and_denies_validator_and_absolute_escape(tmp_path: Path):
    case_root = tmp_path / "case"
    case_root.mkdir()
    workbook = case_root / "input.xlsx"
    workbook.write_bytes(b"fixture")
    validator = tmp_path / "validator.xlsx"
    validator.write_bytes(b"secret")
    scope = ParticipantScope(case_root, denied_paths=(validator,))

    assert scope.read_bytes(workbook) == b"fixture"
    with pytest.raises(PermissionError):
        scope.read_bytes(validator)
    with pytest.raises(PermissionError):
        scope.read_bytes(tmp_path / "outside.xlsx")
