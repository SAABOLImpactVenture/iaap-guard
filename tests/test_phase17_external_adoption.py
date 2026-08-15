import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_external_adoption.py"
SPEC = importlib.util.spec_from_file_location("run_external_adoption", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Phase17ExternalAdoptionTests(unittest.TestCase):
    def write_manifest(self, root: Path, repositories: list[dict]) -> Path:
        path = root / "campaign.json"
        path.write_text(
            json.dumps(
                {
                    "campaignVersion": "external-adoption/v1",
                    "repositories": repositories,
                }
            ),
            encoding="utf-8",
        )
        return path

    def repository(self, name: str = "example/infrastructure", revision: str = "a" * 40) -> dict:
        return {
            "repository": name,
            "revision": revision,
            "ecosystem": "aws",
            "sourceUrl": f"https://github.com/{name}",
        }

    def test_manifest_requires_immutable_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_manifest(root, [self.repository(revision="main")])
            with self.assertRaisesRegex(ValueError, "40-character SHA"):
                MODULE.load_campaign(path)

    def test_manifest_rejects_duplicate_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_manifest(
                root,
                [
                    self.repository(revision="a" * 40),
                    self.repository(revision="b" * 40),
                ],
            )
            with self.assertRaisesRegex(ValueError, "duplicate repository"):
                MODULE.load_campaign(path)

    def test_campaign_scans_checked_out_repository_deterministically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = self.repository()
            manifest_path = self.write_manifest(root, [repository])
            workspace = root / "workspace"
            target = workspace / MODULE.repository_slug(repository["repository"])
            target.mkdir(parents=True)
            (target / "main.tf").write_text(
                'resource "aws_s3_bucket" "example" {\n  bucket = "phase-17-example"\n}\n',
                encoding="utf-8",
            )

            campaign = MODULE.load_campaign(manifest_path)
            first = MODULE.run_campaign(campaign, workspace)
            second = MODULE.run_campaign(campaign, workspace)

            self.assertEqual(first, second)
            self.assertEqual(first["repositoryCount"], 1)
            self.assertEqual(first["ecosystems"], ["aws"])
            result = first["results"][0]
            self.assertEqual(result["repository"], "example/infrastructure")
            self.assertEqual(result["revision"], "a" * 40)
            self.assertEqual(result["scanResult"]["revision"]["sha"], "a" * 40)
            self.assertEqual(result["findingCount"], len(result["scanResult"]["findings"]))


if __name__ == "__main__":
    unittest.main()
