import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


FLAGS = ["touches-trikyn-surface", "db-change", "client-paired", "bots"]

CLIENT_PATH_TOKENS = ["DBC", "dbc", "Extensions", "patch-", "Collections.xml", "FrameXML", "Interface/"]

CLIENT_SUBJECT_PATTERN = re.compile(
    r"\b(client|dbc|display|stream|native|map|zone|world\s+content)\b",
    re.IGNORECASE,
)

SUBJECT_LIMIT = 70


def git(repo, *args):
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout


def load_surface(path):
    surface = {}
    for entry in json.loads(Path(path).read_text(encoding="utf-8")):
        for name in entry.get("files", []):
            surface.setdefault(name, []).append(entry["id"])
    return surface


def commits_in_range(repo, base, head):
    output = git(repo, "log", "--no-merges", "--reverse", "--format=%H%x09%s", f"{base}..{head}")
    return [line.split("\t", 1) for line in output.splitlines() if line]


def changed_files(repo, sha):
    output = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha)
    return [line for line in output.splitlines() if line]


def classify(subject, files, surface):
    surface_hits = sorted({entry for name in files for entry in surface.get(name, [])})
    flags = []
    if surface_hits:
        flags.append("touches-trikyn-surface")
    if any(name.endswith(".sql") or name.startswith("data/sql/") for name in files):
        flags.append("db-change")
    if (any(token in name for name in files for token in CLIENT_PATH_TOKENS)
            or CLIENT_SUBJECT_PATTERN.search(subject)):
        flags.append("client-paired")
    if any(name.startswith("modules/mod-playerbots/") for name in files):
        flags.append("bots")
    return flags, surface_hits


def analyze(repo, base, head, surface=None):
    commits = []
    for sha, subject in commits_in_range(repo, base, head):
        flags, surface_hits = classify(subject, changed_files(repo, sha), surface or {})
        if surface is None:
            flags = [flag for flag in flags if flag != "touches-trikyn-surface"]
            surface_hits = []
        commits.append({"sha": sha, "subject": subject, "flags": flags, "surface_hits": surface_hits})
    counts = {flag: sum(1 for commit in commits if flag in commit["flags"]) for flag in FLAGS}
    return {"commits": commits, "flag_counts": counts, "surface_evaluated": surface is not None}


def truncate_subject(subject):
    if len(subject) <= SUBJECT_LIMIT:
        return subject
    return subject[:SUBJECT_LIMIT - 1] + "…"


def table_cell(text):
    return text.replace("|", "\\|")


def render_markdown(report):
    lines = ["### Upstream fold triage", ""]
    lines.append(f"{len(report['commits'])} commit(s) triaged.")
    for flag in FLAGS:
        lines.append(f"- `{flag}`: {report['flag_counts'][flag]}")
    if not report["surface_evaluated"]:
        lines.append("")
        lines.append("_No customization manifest was supplied; `touches-trikyn-surface` was not evaluated._")
    lines.append("")
    lines.append("| Commit | Subject | Flags | Surface entries |")
    lines.append("| --- | --- | --- | --- |")
    for commit in report["commits"]:
        flags = ", ".join(f"`{flag}`" for flag in commit["flags"]) or "—"
        hits = ", ".join(commit["surface_hits"]) or "—"
        subject = table_cell(truncate_subject(commit["subject"]))
        lines.append(f"| `{commit['sha'][:12]}` | {subject} | {flags} | {hits} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Classify the commits of an upstream fold range against the Trikyn customization surface.")
    parser.add_argument("base", help="Base ref of the fold range.")
    parser.add_argument("head", help="Head ref of the fold range.")
    parser.add_argument("--manifest", help="Local customization manifest JSON; omit to skip surface flagging.")
    parser.add_argument("--repo", default=".", help="Repository to inspect.")
    parser.add_argument("--output", help="Write the JSON report to this file instead of stdout.")
    parser.add_argument("--markdown", action="store_true", help="Print a markdown table instead of JSON.")
    args = parser.parse_args(argv)

    surface = load_surface(args.manifest) if args.manifest else None
    report = analyze(args.repo, args.base, args.head, surface)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    elif not args.markdown:
        print(serialized)
    if args.markdown:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
