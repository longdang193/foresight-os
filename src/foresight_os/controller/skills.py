from dataclasses import dataclass
import hashlib
import importlib.resources
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    version: str
    content_path: str
    content_sha256: str
    capability_ids: tuple[str, ...]
    output_contract: str
    provenance: str


@dataclass(frozen=True)
class ResolvedSkill:
    manifest: SkillManifest
    content: str

    @property
    def skill_id(self) -> str:
        return self.manifest.skill_id

    @property
    def version(self) -> str:
        return self.manifest.version

    @property
    def content_sha256(self) -> str:
        return self.manifest.content_sha256


class SkillRegistry:
    def __init__(self, package: str = "foresight_os.skills") -> None:
        self._package = package
        manifest_path = importlib.resources.files(package).joinpath("manifest.json")
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        self._manifests = {
            item["id"]: SkillManifest(
                skill_id=item["id"],
                version=item["version"],
                content_path=item["content_path"],
                content_sha256=item["content_sha256"],
                capability_ids=tuple(item.get("capability_ids", ())),
                output_contract=item["output_contract"],
                provenance=item["provenance"],
            )
            for item in raw["skills"]
        }

    def manifest(self, skill_id: str) -> SkillManifest:
        try:
            return self._manifests[skill_id]
        except KeyError as exc:
            raise ValueError(f"unknown skill: {skill_id}") from exc

    def resolve(self, skill_ids: tuple[str, ...] | list[str] = ()) -> tuple[ResolvedSkill, ...]:
        resolved = []
        for skill_id in skill_ids:
            manifest = self.manifest(str(skill_id))
            content = importlib.resources.files(self._package).joinpath(manifest.content_path).read_text(encoding="utf-8")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if digest != manifest.content_sha256:
                raise RuntimeError(f"skill content hash mismatch: {manifest.skill_id}")
            resolved.append(ResolvedSkill(manifest, content))
        return tuple(resolved)

    def required_capabilities(self, skills: tuple[ResolvedSkill, ...] | list[ResolvedSkill]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(capability for skill in skills for capability in skill.manifest.capability_ids))

    def instructions(self, skills: tuple[ResolvedSkill, ...] | list[ResolvedSkill]) -> str:
        return "\n\n".join(
            f"## Method: {skill.skill_id} (v{skill.version})\n{skill.content}"
            for skill in skills
        )

    def describe(self, skills: tuple[ResolvedSkill, ...] | list[ResolvedSkill]) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            {
                "id": skill.skill_id,
                "version": skill.version,
                "content_sha256": skill.content_sha256,
                "output_contract": skill.manifest.output_contract,
                "provenance": skill.manifest.provenance,
            }
            for skill in skills
        )
