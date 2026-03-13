from __future__ import annotations

import re


INVALID_CHARS = re.compile(r"[\\/:*?\"<>|\n\r\t]")


def safe_filename(name: str, max_len: int = 128) -> str:
    cleaned = INVALID_CHARS.sub("_", name).strip(" .")
    if not cleaned:
        cleaned = "file"
    if len(cleaned) > max_len:
        stem, dot, ext = cleaned.rpartition(".")
        if dot and stem:
            keep = max_len - len(ext) - 1
            cleaned = f"{stem[:keep]}.{ext}"
        else:
            cleaned = cleaned[:max_len]
    return cleaned


def resolve_attachment_name(name: str, file_id: str, existing: set[str]) -> str:
    candidate = safe_filename(name)
    if candidate not in existing:
        existing.add(candidate)
        return candidate
    stem, dot, ext = candidate.rpartition(".")
    if not dot:
        stem, ext = candidate, ""
    suffix = f"__{file_id}"
    resolved = f"{stem}{suffix}{dot}{ext}" if dot else f"{stem}{suffix}"
    existing.add(resolved)
    return resolved
