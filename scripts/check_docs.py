#!/usr/bin/env python3
"""Documentation checks: relative links resolve, heading anchors exist, and
every page under a content directory declares a valid status marker."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIRS = {"getting-started", "architecture", "protocol", "sdk", "integrations", "ecosystem", "developers", "reference"}
STATUSES = {"Implemented", "Partially implemented", "Planned", "Proposed", "Experimental", "Undecided", "Superseded", "Reference", "Accepted"}
STATUS_RE = re.compile(r"^\*\*Status:\*\* (.+?)\s*$", re.M)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^```.*?^```", re.M | re.S)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.M)


def slug(heading: str) -> str:
    text = re.sub(r"`|\*|_|<[^>]+>", "", heading).strip().lower()
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set:
    text = FENCE_RE.sub("", path.read_text(encoding="utf-8"))
    seen, out = {}, set()
    for h in HEADING_RE.findall(text):
        s = slug(h)
        n = seen.get(s, 0)
        out.add(s if n == 0 else f"{s}-{n}")
        seen[s] = n + 1
    return out


def main() -> int:
    errors = []
    files = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
    cache = {}
    for f in files:
        rel = f.relative_to(ROOT)
        text = f.read_text(encoding="utf-8")
        body = FENCE_RE.sub("", text)
        if rel.parts[0] in CONTENT_DIRS:
            m = STATUS_RE.search(text)
            if not m:
                errors.append(f"{rel}: missing '**Status:** ...' line")
            elif m.group(1).split(" — ")[0].split(" (")[0].strip() not in STATUSES:
                errors.append(f"{rel}: unknown status '{m.group(1)}'")
        for target in LINK_RE.findall(body):
            if re.match(r"[a-z][a-z0-9+.-]*:", target):
                continue
            path_part, _, frag = target.partition("#")
            dest = f if not path_part else (f.parent / path_part).resolve()
            if path_part and not dest.exists():
                errors.append(f"{rel}: broken link '{target}'")
                continue
            if frag and dest.suffix == ".md":
                if dest not in cache:
                    cache[dest] = anchors(dest)
                if frag.lower() not in cache[dest]:
                    errors.append(f"{rel}: missing anchor '{target}'")
    for e in errors:
        print(e)
    print(f"checked {len(files)} files, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
