from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Attachment:
    file_id: str
    topic_id: int
    name: str
    ext: str | None = None
    size_bytes: int | None = None
    download_url: str | None = None
    mime_type: str | None = None
    checksum: str | None = None
    relative_path: str | None = None
    status: str = "pending"


@dataclass
class Article:
    topic_id: int
    column_id: int
    group_id: int
    title: str | None
    author_name: str | None
    created_at: str | None
    modified_at: str | None
    attached_to_column_time: str | None
    source_url: str | None
    body_html: str | None
    body_markdown: str | None
    content_checksum: str
    raw_json_path: str | None
    render_version: str
    attachments: list[Attachment] = field(default_factory=list)


@dataclass(order=True, frozen=True)
class Cursor:
    attached_to_column_time: str
    topic_id: int


@dataclass
class TopicListItem:
    topic_id: int
    attached_to_column_time: str
    modified_at: str | None

    @property
    def cursor(self) -> Cursor:
        return Cursor(self.attached_to_column_time, self.topic_id)


@dataclass
class RunSummary:
    run_id: str
    mode: str
    scanned_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "scanned_count": self.scanned_count,
            "created_count": self.created_count,
            "updated_count": self.updated_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "failures": self.failures,
        }
