from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .models import Article, Attachment, TopicListItem
from .utils.html_to_md import html_to_markdown


class ZsxqClient:
    """Minimal zsxq API client for column list/detail/download resolve."""

    def __init__(self, cookie: str, group_id: int, render_version: str = "v2") -> None:
        self.group_id = group_id
        self.render_version = render_version
        try:
            import requests
            self.session = requests.Session()
        except ModuleNotFoundError:  # pragma: no cover
            raise RuntimeError("requests is required for real network crawling")
        self.session.headers.update({"cookie": cookie, "accept": "application/json"})
        self.base = "https://api.zsxq.com/v2"

    def list_column_topics(self, column_id: int, after: str | None = None, limit: int = 20) -> list[TopicListItem]:
        params: dict[str, Any] = {"count": limit}
        if after:
            params["end_time"] = after
        url = f"{self.base}/groups/{self.group_id}/columns/{column_id}/topics"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        topics = resp.json().get("resp_data", {}).get("topics", [])
        items: list[TopicListItem] = []
        for t in topics:
            topic_id = int(t.get("topic_id") or t.get("id"))
            attached = t.get("attached_to_column_time") or t.get("create_time")
            modified = t.get("modify_time")
            if attached:
                items.append(TopicListItem(topic_id=topic_id, attached_to_column_time=attached, modified_at=modified))
        return items

    def get_topic_detail(self, topic_id: int) -> Article:
        url = f"{self.base}/topics/{topic_id}/info"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        payload = resp.json().get("resp_data", {}).get("topic", {})
        talk = payload.get("talk", {})
        files = talk.get("files", [])
        atts = [
            Attachment(
                file_id=str(f.get("file_id") or f.get("id")),
                topic_id=topic_id,
                name=f.get("name") or "file",
                ext=(f.get("name") or "").split(".")[-1] if "." in (f.get("name") or "") else None,
                size_bytes=f.get("size"),
                mime_type=f.get("mime_type"),
                download_url=f.get("download_url"),
            )
            for f in files
        ]
        body_html = talk.get("text", "")
        body_md = html_to_markdown(body_html)
        checksum = str(abs(hash(body_md)))
        return Article(
            topic_id=topic_id,
            column_id=int(payload.get("column_id") or 0),
            group_id=self.group_id,
            title=talk.get("title"),
            author_name=payload.get("user", {}).get("name"),
            created_at=talk.get("create_time"),
            modified_at=talk.get("modify_time"),
            attached_to_column_time=payload.get("attached_to_column_time"),
            source_url=f"https://wx.zsxq.com/dweb2/index/topic_detail/{topic_id}",
            body_html=body_html,
            body_markdown=body_md,
            content_checksum=checksum,
            raw_json_path=None,
            render_version=self.render_version,
            attachments=atts,
        )

    def resolve_file_download(self, file_id: str) -> dict[str, Any]:
        url = f"{self.base}/files/{file_id}/download_url"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("resp_data", {})

    @staticmethod
    def write_raw(path: Path, article: Article) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(article), ensure_ascii=False, indent=2), encoding="utf-8")
