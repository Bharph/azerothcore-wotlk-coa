from __future__ import annotations

CLI_DESCRIPTION = """Deliver in-game reports to Trikyn: a GitHub issue on the Trikyn tracker plus a Discord card.

Reuses the hardened delivery journal, file lock and status writer from relay.py; only the delivery
backend differs (gh + Discord instead of the community Railway service). Dry-run is the default;
--send performs real GitHub issue creation and Discord posting. Never run two instances against one spool.
"""

import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relay import DeliveryError, Relay, read_report, worker_lock  # noqa: E402

TRACKER = "Bharph/trikyn-live-ops"
BUG_CHANNEL = "1548181106317066281"
FEEDBACK_CHANNEL = "1553546380574720140"
DEFAULT_LABELS = ("type:bug", "area:unknown")
DISCORD_API = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (https://trikyn.online, 1.0)"
TYPE_TAG = re.compile(r"^\s*\[(bug|feedback)\]\s*", re.IGNORECASE)
ISSUE_URL = re.compile(r"/issues/(\d+)")
BUG_COLOR = 0xD73A4A
SPACER_NAME = "spacer.png"


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def build_spacer_png(width: int = 1024, height: int = 1) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    scanlines = (b"\x00" + b"\x00" * (width * 4)) * height
    return (signature + _png_chunk(b"IHDR", header)
            + _png_chunk(b"IDAT", zlib.compress(scanlines, 9)) + _png_chunk(b"IEND", b""))


SPACER_PNG = build_spacer_png()


def classify(title: str):
    match = TYPE_TAG.match(title)
    if match:
        return match.group(1).lower(), title[match.end():].strip() or title.strip()
    return "bug", title.strip()


class TrikynDelivery:
    def __init__(self, token, tracker=TRACKER, bug_channel=BUG_CHANNEL,
                 feedback_channel=FEEDBACK_CHANNEL, labels=DEFAULT_LABELS, project=""):
        self.token = token
        self.tracker = tracker
        self.bug_channel = bug_channel
        self.feedback_channel = feedback_channel
        self.labels = list(labels)
        self.project = project

    def create(self, title: str, body: str) -> int:
        kind, cleaned = classify(title)
        if kind == "feedback":
            raise DeliveryError("invalid")
        number = self._open_issue(cleaned, body)
        self._post_card(self.bug_channel, "In-game bug report", cleaned, body, number)
        return number

    def _open_issue(self, title: str, body: str) -> int:
        command = ["gh", "issue", "create", "--repo", self.tracker, "--title", title, "--body", body]
        for label in self.labels:
            command += ["--label", label]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            raise DeliveryError("uncertain") from None
        if result.returncode != 0:
            raise self._github_failure(result.stderr)
        match = ISSUE_URL.search(result.stdout or "")
        if not match:
            raise DeliveryError("uncertain")
        if self.project:
            self._add_to_board(result.stdout.strip())
        return int(match.group(1))

    @staticmethod
    def _github_failure(stderr: str) -> DeliveryError:
        lowered = (stderr or "").lower()
        if "rate limit" in lowered:
            return DeliveryError("limited", 900)
        blocked = ("authentication", "not logged into", "permission", "forbidden",
                   "http 401", "http 403", "http 404", "could not resolve to a repository")
        if any(term in lowered for term in blocked):
            return DeliveryError("blocked")
        return DeliveryError("uncertain")

    def _add_to_board(self, issue_url: str):
        try:
            subprocess.run(["gh", "project", "item-add", self.project, "--owner", "Bharph", "--url", issue_url],
                           capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            print(f"warning: board add failed for {issue_url}", flush=True)

    def _post_card(self, channel: str, heading: str, title: str, body: str, number: int):
        description = body if len(body) <= 3800 else body[:3800] + "\n… (truncated)"
        embed = {
            "title": f"{heading}: {title}"[:256],
            "description": description or "(no details provided)",
            "color": BUG_COLOR,
            "footer": {"text": f"in-game submission · issue #{number}"},
            "image": {"url": f"attachment://{SPACER_NAME}"},
        }
        payload = {"embeds": [embed], "attachments": [{"id": 0, "filename": SPACER_NAME}]}
        boundary = "----trikyn" + uuid.uuid4().hex
        request = urllib.request.Request(f"{DISCORD_API}/channels/{channel}/messages",
                                         data=self._multipart(boundary, payload, SPACER_PNG), method="POST")
        request.add_header("Authorization", f"Bot {self.token}")
        request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        request.add_header("User-Agent", USER_AGENT)
        try:
            urllib.request.urlopen(request, timeout=20)
        except (urllib.error.URLError, OSError):
            print(f"warning: Discord card post failed for issue #{number}", flush=True)

    @staticmethod
    def _multipart(boundary: str, payload: dict, png: bytes) -> bytes:
        line = b"--" + boundary.encode()
        parts = [
            line, b'Content-Disposition: form-data; name="payload_json"', b"Content-Type: application/json", b"",
            json.dumps(payload).encode("utf-8"),
            line, f'Content-Disposition: form-data; name="files[0]"; filename="{SPACER_NAME}"'.encode(),
            b"Content-Type: image/png", b"", png,
            b"--" + boundary.encode() + b"--", b"",
        ]
        return b"\r\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    parser.add_argument("--spool", type=Path, required=True)
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--tracker", default=TRACKER)
    parser.add_argument("--bug-channel", default=BUG_CHANNEL)
    parser.add_argument("--feedback-channel", default=FEEDBACK_CHANNEL)
    parser.add_argument("--label", action="append")
    parser.add_argument("--project", default="")
    parser.add_argument("--once", action="store_true", help="Process one pass, then exit.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--send", action="store_true", help="Enable real GitHub + Discord delivery.")
    modes.add_argument("--dry-run", action="store_true", help="Validate files without writes or network (default).")
    args = parser.parse_args()
    root = args.spool.resolve(strict=True)
    if not root.is_dir():
        parser.error("--spool must be an existing private directory")
    os.umask(0o077)
    if not args.send:
        count = 0
        for path in sorted(root.glob("*.report")):
            read_report(path)
            count += 1
        print(f"Dry run: {count} report(s) valid; no network requests or file writes.")
        return 0
    if not args.token_file:
        parser.error("--token-file is required with --send")
    token = args.token_file.read_text(encoding="utf-8").strip()
    if not token:
        parser.error("--token-file is empty")
    labels = args.label if args.label else list(DEFAULT_LABELS)
    service = TrikynDelivery(token, args.tracker, args.bug_channel, args.feedback_channel, labels, args.project)
    with worker_lock(root):
        worker = Relay(root, service)
        try:
            while True:
                for path in sorted(root.glob("*.report")):
                    worker.process(path)
                if args.once:
                    break
                time.sleep(5)
        finally:
            worker.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
