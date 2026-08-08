from __future__ import annotations

import io
import unittest

from iaap_guard.github_app import GitHubApi


class _BytesResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class _RecordingOpener:
    def __init__(self, response: bytes):
        self.response = response
        self.requests = []

    def open(self, request, timeout=30):  # noqa: ARG002
        self.requests.append(request)
        return _BytesResponse(self.response)


class Phase10ArchiveAcceptRegressionTests(unittest.TestCase):
    def test_tarball_api_request_uses_github_json_media_type_while_returning_bytes(self):
        opener = _RecordingOpener(b"tarball-bytes")
        api = GitHubApi(opener=opener)

        archive = api.repository_tarball("installation-token", "example/platform", "a" * 40)

        self.assertEqual(archive, b"tarball-bytes")
        request = opener.requests[0]
        self.assertEqual(request.headers["Accept"], "application/vnd.github+json")
        self.assertEqual(request.headers["Authorization"], "Bearer installation-token")


if __name__ == "__main__":
    unittest.main()
