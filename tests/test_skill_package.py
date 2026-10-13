"""Exercise the packaged skill contract without requiring an agent provider."""

import json
from importlib.resources import files
import re
import unittest

from foresight_os.controller.skills import SkillRegistry


class SkillPackageTests(unittest.TestCase):
    REQUIRED_SECTIONS = (
        "Inputs",
        "When to use",
        "Do not use / route instead",
        "Workflow",
        "Output",
        "Completion check",
        "Pair with",
        "Anti-patterns",
    )

    def setUp(self):
        self.package = files("foresight_os.skills")
        self.manifest = json.loads(self.package.joinpath("manifest.json").read_text(encoding="utf-8"))
        self.registry = SkillRegistry()
        self.manifest_by_id = {item["id"]: item for item in self.manifest["skills"]}

    @staticmethod
    def _frontmatter_name(content):
        if not content.startswith("---\n"):
            raise AssertionError("skill content must start with YAML frontmatter")
        frontmatter, _, _ = content[4:].partition("\n---\n")
        match = re.search(r"^name:\s*([^\n]+)\s*$", frontmatter, re.MULTILINE)
        if match is None:
            raise AssertionError("skill frontmatter must declare name")
        return match.group(1).strip()

    @staticmethod
    def _section_body(content, section):
        match = re.search(
            rf"^## {re.escape(section)}\n(?P<body>.*?)(?=^## |\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        if match is None:
            raise AssertionError(f"missing section: {section}")
        return match.group("body")

    def test_every_manifest_entry_resolves_packaged_content(self):
        ids = tuple(item["id"] for item in self.manifest["skills"])
        self.assertEqual(len(ids), len(set(ids)))
        directories = {item.name for item in self.package.iterdir() if item.joinpath("SKILL.md").is_file()}
        self.assertEqual(set(ids), directories)
        resolved = self.registry.resolve(ids)
        self.assertEqual(tuple(skill.skill_id for skill in resolved), ids)
        self.assertTrue(all(skill.content and skill.content_sha256 for skill in resolved))

    def test_manifest_content_matches_frontmatter_and_required_sections(self):
        resolved = self.registry.resolve(tuple(self.manifest_by_id))
        for skill in resolved:
            self.assertEqual(self._frontmatter_name(skill.content), skill.skill_id)
            for section in self.REQUIRED_SECTIONS:
                self.assertTrue(self._section_body(skill.content, section).strip())

    def test_pair_with_references_resolve_only_from_backticked_identifiers(self):
        known_ids = set(self.manifest_by_id)
        for skill in self.registry.resolve(tuple(self.manifest_by_id)):
            pair_with = self._section_body(skill.content, "Pair with")
            referenced_ids = set(re.findall(r"`([a-z0-9-]+)`", pair_with))
            self.assertTrue(referenced_ids <= known_ids)

    def test_declared_skill_capability_boundaries_are_least_privilege(self):
        self.assertEqual(self.registry.required_capabilities(self.registry.resolve(("source-appraisal",))), ())
        self.assertEqual(self.registry.required_capabilities(self.registry.resolve(("presentation-storytelling",))), ())
        self.assertEqual(self.registry.required_capabilities(self.registry.resolve(("slide-design-review",))), ())
        self.assertEqual(
            self.registry.required_capabilities(self.registry.resolve(("evidence-visualization",))),
            ("data_analysis", "calculation"),
        )

    def test_skill_prompt_sizes_have_only_an_upper_bound(self):
        combinations = (
            ("red-team-claim",),
            ("red-team-claim", "key-assumptions-check"),
            ("presentation-storytelling", "evidence-visualization"),
        )
        for skill_ids in tuple((skill.skill_id,) for skill in self.registry.resolve(tuple(self.manifest_by_id))):
            instructions = self.registry.instructions(self.registry.resolve(skill_ids))
            word_count = len(instructions.split())
            byte_size = len(instructions.encode("utf-8"))
            self.assertLessEqual(word_count, 700, skill_ids)
            self.assertGreater(word_count, 0, skill_ids)
            self.assertGreater(byte_size, 0, skill_ids)
        for skill_ids in combinations:
            instructions = self.registry.instructions(self.registry.resolve(skill_ids))
            self.assertGreater(len(instructions.split()), 0, skill_ids)
            self.assertGreater(len(instructions.encode("utf-8")), 0, skill_ids)

    def test_presentation_planning_and_review_do_not_require_external_writes(self):
        registry = SkillRegistry()
        skills = registry.resolve(("presentation-storytelling", "slide-design-review"))
        self.assertEqual(registry.required_capabilities(skills), ())
        self.assertEqual(tuple(item["id"] for item in registry.describe(skills)),
                         ("presentation-storytelling", "slide-design-review"))

    def test_visualization_uses_existing_deterministic_capabilities(self):
        registry = SkillRegistry()
        skills = registry.resolve(("quantitative-sanity-check", "evidence-visualization"))
        self.assertEqual(registry.required_capabilities(skills), ("data_analysis", "calculation"))

    def test_presentation_skill_instructions_stay_selected(self):
        registry = SkillRegistry()
        instructions = registry.instructions(registry.resolve(("presentation-storytelling",)))
        self.assertIn("# Presentation Storytelling", instructions)
        self.assertNotIn("# Slide Design Review", instructions)
        self.assertNotIn("# Red-Team Claim", instructions)


if __name__ == "__main__":
    unittest.main()
