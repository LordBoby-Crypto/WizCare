"""Lightweight GUI-side validation for Deimos bot editor scripts.

This module intentionally performs conservative, local checks only. It does not
try to execute bot code, import game clients, or infer full Wizard101 strategy.
The goal is to catch empty scripts, malformed metadata, risky combat markers, and
obvious command-shape mistakes before the GUI queues ExecuteBot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

_CLIENT_SELECTOR_RE = re.compile(r"^p(?:[1-9]|1[0-9]|2[0-9]|3[0-2])$", re.IGNORECASE)
_COMBAT_MARKER_RE = re.compile(r"^#{3}\s*p(?P<client>[1-9][0-9]*)\s*$", re.IGNORECASE)
_METADATA_RE = re.compile(r"^\s*@(?P<key>[a-zA-Z0-9_.-]+)\s*[:=]\s*(?P<value>.*?)\s*$")
_COORD_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

_KNOWN_METADATA_KEYS = {
    "clients", "world", "zone", "location", "quest", "boss", "enemy",
    "school", "level", "goal", "author", "description", "requires", "notes",
}

_KNOWN_COMMANDS = {
    "goto", "go", "walk", "walkto", "teleport", "tp", "tozone", "zone",
    "wait", "sleep", "waitforzone", "waitforcombat", "waitforfree",
    "battle", "combat", "kill", "interact", "dialogue", "quest", "collect",
    "follow", "friendtp", "setplaystyle", "playstyle", "sigil", "mark", "recall",
    "sendkey", "click", "camera", "orient", "xyz", "usepotion", "logdrop",
}

@dataclass(slots=True)
class BotValidationIssue:
    severity: str
    line: int
    code: str
    message: str

@dataclass(slots=True)
class BotValidationResult:
    ok: bool
    errors: list[BotValidationIssue] = field(default_factory=list)
    warnings: list[BotValidationIssue] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def issue_count(self) -> int:
        return len(self.errors) + len(self.warnings)

    def summary(self) -> str:
        if not self.issue_count:
            return "Bot validation passed."
        return f"Bot validation found {len(self.errors)} error(s) and {len(self.warnings)} warning(s)."

    def format_details(self, limit: int = 12) -> str:
        issues = [*self.errors, *self.warnings]
        if not issues:
            return self.summary()
        lines = [self.summary()]
        for issue in issues[:limit]:
            location = f"line {issue.line}" if issue.line else "script"
            lines.append(f"[{issue.severity.upper()}] {location}: {issue.message}")
        remaining = len(issues) - limit
        if remaining > 0:
            lines.append(f"...and {remaining} more issue(s).")
        return "\n".join(lines)


def validate_bot_script(script: str) -> BotValidationResult:
    """Validate raw bot editor text before ExecuteBot is queued.

    The checks are intentionally conservative. Unknown commands are warnings, not
    errors, because Deimos supports multiple command surfaces and aliases.
    """
    errors: list[BotValidationIssue] = []
    warnings: list[BotValidationIssue] = []
    metadata: dict[str, str] = {}

    def add_error(line: int, code: str, message: str) -> None:
        errors.append(BotValidationIssue("error", line, code, message))

    def add_warning(line: int, code: str, message: str) -> None:
        warnings.append(BotValidationIssue("warning", line, code, message))

    if not script or not script.strip():
        add_error(0, "empty-script", "Bot script is empty.")
        return BotValidationResult(False, errors, warnings, metadata)

    saw_executable_line = False
    saw_combat_marker = False

    for line_no, raw_line in enumerate(script.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") and not line.startswith("###"):
            continue

        marker = _COMBAT_MARKER_RE.match(line)
        if marker:
            saw_combat_marker = True
            client_num = int(marker.group("client"))
            if client_num > 32:
                add_error(line_no, "combat-marker-client-range", "Combat marker client number is above supported validator range p1-p32.")
            continue

        meta = _METADATA_RE.match(line)
        if meta:
            key = meta.group("key").lower()
            value = meta.group("value")
            metadata[key] = value
            if key not in _KNOWN_METADATA_KEYS:
                add_warning(line_no, "unknown-metadata", f"Unknown bot metadata key '@{key}'.")
            if key == "clients":
                selectors = [part.strip() for part in re.split(r"[,\s]+", value) if part.strip()]
                bad = [selector for selector in selectors if not _CLIENT_SELECTOR_RE.match(selector)]
                if bad:
                    add_error(line_no, "bad-client-selector", f"Unsupported client selector(s): {', '.join(bad)}.")
            continue

        saw_executable_line = True
        parts = line.split()
        command = parts[0].lower().rstrip(":")
        args = parts[1:]

        if command not in _KNOWN_COMMANDS:
            add_warning(line_no, "unknown-command", f"Unknown command '{parts[0]}'; verify this is a supported Deimos command or alias.")

        if command in {"goto", "go", "walk", "walkto", "teleport", "tp", "xyz"}:
            nums = [a.strip(",") for a in args if _COORD_RE.match(a.strip(","))]
            if len(nums) not in {0, 2, 3, 4, 6}:
                add_warning(line_no, "coordinate-shape", "Movement/coordinate command has an unusual number of numeric arguments.")

        if command in {"wait", "sleep"} and args:
            value = args[0].strip(",")
            if _COORD_RE.match(value):
                try:
                    seconds = float(value)
                    if seconds < 0:
                        add_error(line_no, "negative-wait", "Wait duration cannot be negative.")
                    elif seconds > 600:
                        add_warning(line_no, "long-wait", "Wait duration is over 10 minutes; verify this is intentional.")
                except ValueError:
                    pass

        if command in {"tozone", "zone", "waitforzone"} and not args:
            add_error(line_no, "missing-zone", f"Command '{parts[0]}' requires a zone/location argument.")

    if not saw_executable_line and not saw_combat_marker:
        add_error(0, "no-actions", "Bot script has metadata/comments only and no executable bot actions.")

    if saw_combat_marker and "clients" not in metadata:
        add_warning(0, "combat-without-client-metadata", "Combat markers were found, but no @clients metadata was declared.")

    return BotValidationResult(not errors, errors, warnings, metadata)
