"""Portable artifact tests; run with python -m unittest discover -s Scripts -p test_mql_skill_package.py."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

SKILL = "plugins/mnemic/skills/mql"
REFERENCE = SKILL + "/references"
MANIFEST = "plugins/mnemic/.claude-plugin/plugin.json"


class SkillPackageTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("package_mql_skill", Path(__file__).with_name("package_mql_skill.py"))
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(prefix="mql-skill-package-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.write(MANIFEST, '{\n  "name": "mnemic",\n  "version": "1.2.3"\n}\n')
        self.write(SKILL + "/SKILL.md", "---\nname: mql\ndescription: Author MQL.\n---\n\n[Queries](references/MqlReference/queries.md#basic-queries)\n")
        self.write(REFERENCE + "/README.md", "# Documentation\n\n- [Configuration](configuration.md)\n- [MQL reference](MqlReference/README.md)\n")
        self.write(REFERENCE + "/configuration.md", "# Configuration\n\n## Standalone server environment\n")
        self.write(REFERENCE + "/MqlReference/README.md", "# MQL reference\n\n- [Queries](queries.md)\n")
        self.write(REFERENCE + "/MqlReference/queries.md", "# Queries\n\n## Basic queries\n\n[Details](other.md#details), [the environment](../configuration.md#standalone-server-environment) and [the site](https://mnemic.io/docs/).\n")
        self.write(REFERENCE + "/MqlReference/other.md", "# Details\n\nUse bracketed identifiers.\n")
        # What a submodule checkout keeps beside the manual.
        self.write(REFERENCE + "/.git", "gitdir: ../../../../.git/modules/plugins/mnemic/skills/mql/references\n")
        self.write(REFERENCE + "/.github/notes.md", "# Repository notes\n")
        self.commit = "a" * 40
        self.reference_commit = "b" * 40

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.replace("\n", "\r\n").encode())

    def package(self, name="output"):
        return self.module.build(self.root, self.commit, self.reference_commit, Path(self.temp.name) / name)

    def test_self_contained_deterministic_archive_of_the_pinned_manual(self):
        archive = self.package()
        self.assertEqual("Mnemic.Mql.Skill-1.2.3.zip", archive.name)
        self.assertEqual(archive.read_bytes(), self.package("second").read_bytes())
        with zipfile.ZipFile(archive) as zipped:
            names = zipped.namelist()
            self.assertEqual(sorted(["mql/SKILL.md", "mql/package.json", "mql/references/README.md", "mql/references/configuration.md",
                                     "mql/references/MqlReference/README.md", "mql/references/MqlReference/other.md",
                                     "mql/references/MqlReference/queries.md"]), sorted(names))
            text = zipped.read("mql/references/MqlReference/queries.md").decode()
            self.assertIn("(other.md#details)", text)
            self.assertIn("(../configuration.md#standalone-server-environment)", text)
            self.assertIn("(https://mnemic.io/docs/)", text)
            manifest = json.loads(zipped.read("mql/package.json"))
            self.assertEqual(self.commit, manifest["commit"])
            self.assertEqual(self.reference_commit, manifest["referenceCommit"])
            self.assertEqual("1.2.3", manifest["version"])
            for entry in zipped.infolist():
                self.assertNotEqual(0o120000, (entry.external_attr >> 16) & 0o170000)
            extracted = Path(self.temp.name) / "isolated"
            zipped.extractall(extracted)
        self.module.verify(archive, self.root, self.commit, self.reference_commit)
        self.module.validate_links({name: (extracted / name).read_bytes() for name in names if name.endswith(".md")})

    def test_package_carries_the_plugin_version(self):
        self.write(MANIFEST, '{\n  "name": "mnemic",\n  "version": "2.0.0-rc.1"\n}\n')
        archive = self.package()
        self.assertEqual("Mnemic.Mql.Skill-2.0.0-rc.1.zip", archive.name)
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual("2.0.0-rc.1", json.loads(zipped.read("mql/package.json"))["version"])

    def test_invalid_plugin_version_is_rejected(self):
        self.write(MANIFEST, '{\n  "name": "mnemic",\n  "version": "1.2"\n}\n')
        with self.assertRaisesRegex(ValueError, "SemVer"):
            self.package()

    def test_missing_local_file_is_rejected(self):
        self.write(REFERENCE + "/MqlReference/other.md", "# Details\n[Missing](missing.md)\n")
        with self.assertRaisesRegex(ValueError, "missing"):
            self.package()

    def test_missing_heading_is_rejected(self):
        self.write(REFERENCE + "/MqlReference/other.md", "# Changed heading\n")
        with self.assertRaisesRegex(ValueError, "details"):
            self.package()

    def test_link_leaving_the_package_is_rejected(self):
        self.write(REFERENCE + "/MqlReference/other.md", "# Details\n\n[Design](../../Decisions/query.md)\n")
        with self.assertRaisesRegex(ValueError, "missing bundled target"):
            self.package()

    def test_uninitialized_manual_is_rejected(self):
        shutil.rmtree(self.root / REFERENCE)
        (self.root / REFERENCE).mkdir()
        with self.assertRaisesRegex(ValueError, "initialize the submodule"):
            self.package()

    def test_stale_source_is_rejected(self):
        archive = self.package()
        self.write(REFERENCE + "/MqlReference/other.md", "# Details\nChanged content.\n")
        with self.assertRaises(ValueError):
            self.module.verify(archive, self.root, self.commit, self.reference_commit)

    def test_other_reference_commit_is_rejected(self):
        archive = self.package()
        with self.assertRaises(ValueError):
            self.module.verify(archive, self.root, self.commit, "c" * 40)

    def test_archive_path_escape_is_rejected(self):
        archive = self.package()
        with zipfile.ZipFile(archive, "a") as zipped:
            zipped.writestr("../escape.md", "escape")
        with self.assertRaises(ValueError):
            self.module.verify(archive, self.root, self.commit, self.reference_commit)

    def test_existing_artifact_is_not_overwritten(self):
        self.package()
        with self.assertRaises(FileExistsError):
            self.package()

    def test_lf_and_crlf_checkouts_produce_identical_artifacts(self):
        first = self.package().read_bytes()
        for path in self.root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
        self.assertEqual(first, self.package("lf-output").read_bytes())

    def test_missing_skill_frontmatter_is_rejected(self):
        self.write(SKILL + "/SKILL.md", "# Just a document\n")
        with self.assertRaisesRegex(ValueError, "frontmatter"):
            self.package()


if __name__ == "__main__":
    unittest.main()
