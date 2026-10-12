import json
from importlib.resources import files


def test_packaged_schema_resources_are_loadable_outside_source_layout():
    analysis = json.loads(files("foresight_os.schemas").joinpath("analysis.schema.json").read_text(encoding="utf-8"))
    work_brief = json.loads(files("foresight_os.schemas").joinpath("work_brief.schema.json").read_text(encoding="utf-8"))

    assert analysis["title"] == "Foresight OS Analysis State"
    assert work_brief["title"] == "Foresight OS Work Brief"
