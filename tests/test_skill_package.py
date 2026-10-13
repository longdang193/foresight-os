"""Exercise the packaged skill contract without requiring an agent provider."""

import json
from importlib.resources import files
import unittest

from foresight_os.controller.skills import SkillRegistry


class SkillPackageTests(unittest.TestCase):
    def test_every_manifest_entry_resolves_packaged_content(self):
        package = files("foresight_os.skills")
        manifest = json.loads(package.joinpath("manifest.json").read_text(encoding="utf-8"))
        ids = tuple(item["id"] for item in manifest["skills"])
        self.assertEqual(len(ids), len(set(ids)))
        directories = {item.name for item in package.iterdir() if item.joinpath("SKILL.md").is_file()}
        self.assertEqual(set(ids), directories)
        resolved = SkillRegistry().resolve(ids)
        self.assertEqual(tuple(skill.skill_id for skill in resolved), ids)
        self.assertTrue(all(skill.content and skill.content_sha256 for skill in resolved))

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
