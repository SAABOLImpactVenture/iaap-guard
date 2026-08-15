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

    def test_repository_campaign_is_pinned_and_cross_cloud(self):
        campaign = MODULE.load_campaign(ROOT / "config" / "external-adoption-v1.json")
        self.assertEqual(len(campaign["repositories"]), 3)
        self.assertEqual(
            {item["ecosystem"] for item in campaign["repositories"]},
            {"aws", "azure", "gcp"},
        )
        self.assertTrue(all(MODULE.SHA_RE.fullmatch(item["revision"]) for item in campaign["repositories"]))

    def test_workflow_is_manual_read_only_and_sha_pinned(self):
        workflow = (ROOT / ".github" / "workflows" / "external-adoption.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("test \"$GITHUB_REF\" = \"refs/heads/main\"", workflow)
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", workflow)
        self.assertIn("actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("id-token: write", workflow)

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
