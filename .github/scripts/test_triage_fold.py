import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import triage_fold


MANIFEST = [
    {"id": "satchel-rule", "files": ["src/server/coa/CoASatchel.cpp"], "category": "gameplay"},
    {"id": "resurrect-name", "files": ["src/server/game/Handlers/MiscHandler.cpp"], "category": "fix"},
    {"id": "launcher-overlay", "files": ["src/server/coa/CoASatchel.cpp", "conf/dist/overlay.conf"],
     "category": "client"},
]


class TriageFoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.addClassCleanup(cls.tempdir.cleanup)
        cls.repo = cls.tempdir.name
        cls.manifest_path = str(Path(cls.repo) / "fold-manifest.json")
        Path(cls.manifest_path).write_text(json.dumps(MANIFEST), encoding="utf-8")
        cls.git("init", "-q", "-b", "main")
        cls.base = cls.commit("chore: baseline", "README.md")
        cls.commit("fix: keep one buff of an exclusive pair", "src/server/coa/CoASatchel.cpp")
        cls.commit("fix: creature loot rows", "data/sql/updates/db_world/loot.sql")
        cls.commit("chore: seed data", "seed.sql")
        cls.commit("feat: rework talent frame", "Interface/FrameXML/TalentFrame.xml")
        cls.commit("feat: native rendering hook", "src/server/game/Rendering.cpp")
        cls.commit("fix: interrupt coordination in groups", "modules/mod-playerbots/src/Coordination.cpp")
        cls.commit("feat: dbc-backed satchel loot for bot groups " + "x" * 60,
                   "src/server/coa/CoASatchel.cpp", "data/sql/updates/db_world/satchel.sql",
                   "modules/mod-playerbots/src/Satchel.cpp")
        cls.commit("docs: plain notes", "docs/notes.txt")
        cls.git("checkout", "-q", "-b", "side", cls.base)
        cls.commit("fix: side quest text", "side.txt")
        cls.git("checkout", "-q", "main")
        cls.git("merge", "-q", "--no-ff", "-m", "merge: side into main", "side")
        cls.head = cls.rev_parse("HEAD")

    @classmethod
    def git(cls, *args):
        subprocess.run(
            ["git", "-C", cls.repo, "-c", "user.name=Triage", "-c", "user.email=triage@example.com",
             "-c", "commit.gpgsign=false", *args],
            check=True, capture_output=True, text=True,
        )

    @classmethod
    def rev_parse(cls, ref):
        result = subprocess.run(["git", "-C", cls.repo, "rev-parse", ref],
                                check=True, capture_output=True, text=True)
        return result.stdout.strip()

    @classmethod
    def commit(cls, subject, *names):
        for name in names:
            path = Path(cls.repo) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(subject + "\n")
        cls.git("add", "-A")
        cls.git("commit", "-q", "-m", subject)
        return cls.rev_parse("HEAD")

    def report(self, manifest=True):
        surface = triage_fold.load_surface(self.manifest_path) if manifest else None
        return triage_fold.analyze(self.repo, self.base, self.head, surface)

    def flags_by_subject(self, report):
        return {commit["subject"]: commit["flags"] for commit in report["commits"]}

    def test_each_flag_is_detected(self):
        flags = self.flags_by_subject(self.report())
        self.assertEqual(flags["fix: keep one buff of an exclusive pair"], ["touches-trikyn-surface"])
        self.assertEqual(flags["fix: creature loot rows"], ["db-change"])
        self.assertEqual(flags["chore: seed data"], ["db-change"])
        self.assertEqual(flags["feat: rework talent frame"], ["client-paired"])
        self.assertEqual(flags["feat: native rendering hook"], ["client-paired"])
        self.assertEqual(flags["fix: interrupt coordination in groups"], ["bots"])
        self.assertEqual(flags["docs: plain notes"], [])
        self.assertEqual(flags["fix: side quest text"], [])

    def test_multi_flag_commit_reports_every_flag_and_all_surface_entries(self):
        report = self.report()
        commit = next(entry for entry in report["commits"] if entry["subject"].startswith("feat: dbc-backed"))
        self.assertEqual(commit["flags"], triage_fold.FLAGS)
        self.assertEqual(commit["surface_hits"], ["launcher-overlay", "satchel-rule"])

    def test_merge_commits_are_excluded(self):
        self.assertNotIn("merge: side into main", self.flags_by_subject(self.report()))

    def test_flag_counts_aggregate_over_commits(self):
        self.assertEqual(self.report()["flag_counts"], {
            "touches-trikyn-surface": 2,
            "db-change": 3,
            "client-paired": 3,
            "bots": 2,
        })

    def test_surface_entries_match_manifest_ids(self):
        report = self.report()
        commit = next(entry for entry in report["commits"]
                      if entry["subject"] == "fix: keep one buff of an exclusive pair")
        self.assertEqual(commit["surface_hits"], ["launcher-overlay", "satchel-rule"])

    def test_without_manifest_surface_flag_is_skipped(self):
        report = self.report(manifest=False)
        self.assertFalse(report["surface_evaluated"])
        self.assertEqual(report["flag_counts"]["touches-trikyn-surface"], 0)
        self.assertTrue(all(commit["surface_hits"] == [] for commit in report["commits"]))
        self.assertIn("not evaluated", triage_fold.render_markdown(report))

    def test_markdown_summary_table_and_truncation(self):
        report = self.report()
        markdown = triage_fold.render_markdown(report)
        lines = markdown.splitlines()
        self.assertEqual(lines[0], "### Upstream fold triage")
        self.assertIn("9 commit(s) triaged.", lines)
        for flag, count in report["flag_counts"].items():
            self.assertIn(f"- `{flag}`: {count}", lines)
        header = lines.index("| Commit | Subject | Flags | Surface entries |")
        self.assertEqual(lines[header + 1], "| --- | --- | --- | --- |")
        rows = lines[header + 2:]
        self.assertEqual(len(rows), len(report["commits"]))
        truncated = next(row for row in rows if "feat: dbc-backed" in row)
        subject = truncated.split(" | ")[1]
        self.assertEqual(len(subject), triage_fold.SUBJECT_LIMIT)
        self.assertTrue(subject.endswith("…"))
        self.assertIn("`touches-trikyn-surface`, `db-change`, `client-paired`, `bots`", truncated)
        self.assertIn("launcher-overlay, satchel-rule", truncated)
        plain = next(row for row in rows if "docs: plain notes" in row)
        self.assertIn("| — | — |", plain)

    def test_subject_pipes_are_escaped(self):
        self.assertEqual(triage_fold.table_cell("a | b"), "a \\| b")

    def test_classification_heuristics(self):
        for subject, files, expected in (
            ("merge map updates", [], ["client-paired"]),
            ("World Content pass", ["docs/a.txt"], ["client-paired"]),
            ("fix roadmap wording", ["docs/a.txt"], []),
            ("fix displays", ["docs/a.txt"], []),
            ("update", ["patch-B.MPQ"], ["client-paired"]),
            ("update", ["tools/Extensions/build.py"], ["client-paired"]),
            ("update", ["Collections.xml"], ["client-paired"]),
            ("update", ["client/dbc/Spell.dbc"], ["client-paired"]),
            ("update", ["data/sql/base/world.sql"], ["db-change"]),
            ("update", ["modules/mod-playerbots/README.md"], ["bots"]),
            ("update", ["modules/mod-other/src/a.cpp"], []),
        ):
            with self.subTest(subject=subject, files=files):
                flags, hits = triage_fold.classify(subject, files, {})
                self.assertEqual(flags, expected)
                self.assertEqual(hits, [])

    def test_main_writes_json_report_and_prints_markdown(self):
        output_path = Path(self.repo) / "triage.json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = triage_fold.main([
                self.base, self.head, "--repo", self.repo, "--manifest", self.manifest_path,
                "--output", str(output_path), "--markdown",
            ])
        self.assertEqual(status, 0)
        self.assertTrue(stdout.getvalue().startswith("### Upstream fold triage"))
        report = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(report["flag_counts"]["bots"], 2)
        self.assertEqual({commit["sha"] for commit in report["commits"]},
                         {commit["sha"] for commit in self.report()["commits"]})

    def test_main_prints_json_to_stdout_by_default(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = triage_fold.main([self.base, self.head, "--repo", self.repo])
        self.assertEqual(status, 0)
        report = json.loads(stdout.getvalue())
        self.assertFalse(report["surface_evaluated"])
        self.assertEqual(len(report["commits"]), 9)

    def test_empty_range_reports_no_commits(self):
        report = triage_fold.analyze(self.repo, self.head, self.head, {})
        self.assertEqual(report["commits"], [])
        self.assertEqual(report["flag_counts"], {flag: 0 for flag in triage_fold.FLAGS})
        self.assertIn("0 commit(s) triaged.", triage_fold.render_markdown(report))

    def test_git_failure_exits_with_git_status(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as error:
                triage_fold.git(self.repo, "log", "not-a-ref")
        self.assertNotEqual(error.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
