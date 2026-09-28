import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("trikyn_relay", ROOT / "apps/coa-bugreport/trikyn_relay.py")
trikyn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trikyn)
ID = "1-" + "a" * 32
FB_ID = "2-" + "b" * 32


def gh_result(returncode=0, stdout="", stderr=""):
    return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ClassifyTests(unittest.TestCase):
    def test_no_tag_is_bug(self):
        self.assertEqual(trikyn.classify("Pet will not follow"), ("bug", "Pet will not follow"))

    def test_bug_tag_stripped(self):
        self.assertEqual(trikyn.classify("[BUG] Pet will not follow"), ("bug", "Pet will not follow"))

    def test_feedback_tag_detected(self):
        self.assertEqual(trikyn.classify("[Feedback] Love the realm"), ("feedback", "Love the realm"))


class SpacerTests(unittest.TestCase):
    def test_spacer_is_a_valid_wide_png(self):
        png = trikyn.build_spacer_png(1024, 1)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(png[16:24], (1024).to_bytes(4, "big") + (1).to_bytes(4, "big"))


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.service = trikyn.TrikynDelivery("token", tracker="Bharph/trikyn-live-ops")

    def test_bug_creates_issue_with_labels_and_posts_card(self):
        created = "https://github.com/Bharph/trikyn-live-ops/issues/37\n"
        with patch.object(trikyn.subprocess, "run", return_value=gh_result(stdout=created)) as run, \
                patch.object(trikyn.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            number = self.service.create("Pet will not follow", "It just stands there\n")
        self.assertEqual(number, 37)
        command = run.call_args[0][0]
        self.assertEqual(command[:5], ["gh", "issue", "create", "--repo", "Bharph/trikyn-live-ops"])
        self.assertIn("type:bug", command)
        self.assertIn("area:unknown", command)
        self.assertEqual(urlopen.call_count, 1)

    def test_feedback_is_rejected_by_create(self):
        with patch.object(trikyn.subprocess, "run") as run:
            with self.assertRaises(trikyn.DeliveryError) as caught:
                self.service.create("[FEEDBACK] Nice work", "keep it up")
        self.assertEqual(caught.exception.kind, "invalid")
        run.assert_not_called()

    def test_auth_failure_is_blocked(self):
        with patch.object(trikyn.subprocess, "run",
                          return_value=gh_result(returncode=1, stderr="HTTP 403: Forbidden")):
            with self.assertRaises(trikyn.DeliveryError) as caught:
                self.service.create("Title here", "body")
        self.assertEqual(caught.exception.kind, "blocked")

    def test_rate_limit_is_limited(self):
        with patch.object(trikyn.subprocess, "run",
                          return_value=gh_result(returncode=1, stderr="API rate limit exceeded")):
            with self.assertRaises(trikyn.DeliveryError) as caught:
                self.service.create("Title here", "body")
        self.assertEqual(caught.exception.kind, "limited")

    def test_unparseable_success_is_uncertain(self):
        with patch.object(trikyn.subprocess, "run", return_value=gh_result(stdout="no url here")):
            with self.assertRaises(trikyn.DeliveryError) as caught:
                self.service.create("Title here", "body")
        self.assertEqual(caught.exception.kind, "uncertain")

    def test_missing_gh_binary_is_uncertain(self):
        with patch.object(trikyn.subprocess, "run", side_effect=OSError("no gh")):
            with self.assertRaises(trikyn.DeliveryError) as caught:
                self.service.create("Title here", "body")
        self.assertEqual(caught.exception.kind, "uncertain")

    def test_card_failure_does_not_fail_bug_delivery(self):
        created = "https://github.com/Bharph/trikyn-live-ops/issues/41\n"
        with patch.object(trikyn.subprocess, "run", return_value=gh_result(stdout=created)), \
                patch.object(trikyn.urllib.request, "urlopen", side_effect=OSError("discord down")):
            number = self.service.create("Title here", "body")
        self.assertEqual(number, 41)

    def test_feedback_posts_card_without_issue(self):
        with patch.object(trikyn.subprocess, "run") as run, \
                patch.object(trikyn.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            self.service.deliver_feedback("[FEEDBACK] Great server", "love it")
        run.assert_not_called()
        self.assertEqual(urlopen.call_count, 1)

    def test_feedback_card_failure_raises(self):
        with patch.object(trikyn.urllib.request, "urlopen", side_effect=OSError("discord down")):
            with self.assertRaises(trikyn.DeliveryError):
                self.service.deliver_feedback("[FEEDBACK] hi", "there")


class FeedbackFlowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="trikyn-fb-test-")
        self.root = Path(self.temporary.name)
        self.path = self.root / (FB_ID + ".report")
        self.path.write_bytes(b"COABUG1\n[FEEDBACK] Love it\nGreat server, keep going\n")
        self.service = trikyn.TrikynDelivery("token")

    def tearDown(self):
        self.temporary.cleanup()

    def status(self):
        return self.path.with_suffix(".status").read_text().strip()

    def test_is_feedback_detects_tag(self):
        self.assertTrue(trikyn.is_feedback(self.path))

    def test_feedback_flows_to_posted_and_dedups(self):
        with patch.object(trikyn.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            self.assertEqual(trikyn.process_feedback(self.root, self.path, self.service), "posted")
            self.assertEqual(self.status(), "posted")
            self.assertEqual(trikyn.process_feedback(self.root, self.path, self.service), "posted")
        self.assertEqual(urlopen.call_count, 1)

    def test_feedback_transient_failure_retries_without_status(self):
        with patch.object(trikyn.urllib.request, "urlopen", side_effect=OSError("down")):
            self.assertEqual(trikyn.process_feedback(self.root, self.path, self.service), "queued")
        self.assertFalse(self.path.with_suffix(".status").exists())
        with patch.object(trikyn.urllib.request, "urlopen", return_value=FakeResponse()):
            self.assertEqual(trikyn.process_feedback(self.root, self.path, self.service), "posted")
        self.assertEqual(self.status(), "posted")

    def test_feedback_terminal_failure_marks_failed_not_retried(self):
        err = trikyn.urllib.error.HTTPError("https://x", 403, "Forbidden", {}, None)
        with patch.object(trikyn.urllib.request, "urlopen", side_effect=err):
            self.assertEqual(trikyn.process_feedback(self.root, self.path, self.service), "failed")
        self.assertEqual(self.status(), "failed")


class JournalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="trikyn-relay-test-")
        self.root = Path(self.temporary.name)
        self.path = self.root / (ID + ".report")
        self.path.write_bytes(b"COABUG1\nAbility fails\nExpected: damage\nActual: nothing\n")
        self.now = 10000
        self.service = trikyn.TrikynDelivery("token")
        self.worker = trikyn.Relay(self.root, self.service, lambda: self.now)

    def tearDown(self):
        self.worker.close()
        self.temporary.cleanup()

    def status(self):
        return self.path.with_suffix(".status").read_text().strip()

    def test_report_flows_to_created_and_does_not_repost(self):
        created = "https://github.com/Bharph/trikyn-live-ops/issues/37\n"
        with patch.object(trikyn.subprocess, "run", return_value=gh_result(stdout=created)) as run, \
                patch.object(trikyn.urllib.request, "urlopen", return_value=FakeResponse()):
            self.assertEqual(self.worker.process(self.path), "created")
            self.assertEqual(self.status(), "created|37")
            self.worker.process(self.path)
        self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
