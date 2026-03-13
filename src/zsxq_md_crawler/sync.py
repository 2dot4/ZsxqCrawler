from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from .config import AppConfig
from .downloader import AttachmentDownloader
from .exporter import export_article
from .models import Article, Cursor, RunSummary, TopicListItem
from .state_store import StateStore


class SyncService:
    def __init__(self, client, config: AppConfig, state: StateStore, downloader: AttachmentDownloader | None = None) -> None:
        self.client = client
        self.config = config
        self.state = state
        self.downloader = downloader or AttachmentDownloader()

    @staticmethod
    def _should_process(cursor: Cursor | None, item: TopicListItem) -> bool:
        if cursor is None:
            return True
        return item.cursor > cursor

    def _needs_export(self, article: Article, old_row) -> str:
        if old_row is None:
            return "create"
        if old_row["modified_at"] != article.modified_at:
            return "update"
        if old_row["content_checksum"] != article.content_checksum:
            return "update"
        if old_row["render_version"] != article.render_version:
            return "update"
        return "skip"

    def crawl(self, mode: str = "incremental", max_items: int | None = None) -> RunSummary:
        run_id = uuid4().hex
        summary = RunSummary(run_id=run_id, mode=mode)
        self.state.begin_run(run_id, mode)

        cursor = None if mode == "full" else self.state.get_cursor()
        items = self.client.list_column_topics(self.config.column_id, limit=self.config.page_size)
        items = sorted(items, key=lambda i: (i.attached_to_column_time, i.topic_id))

        processed = 0
        for item in items:
            if max_items and processed >= max_items:
                break
            summary.scanned_count += 1
            if not self._should_process(cursor, item):
                summary.skipped_count += 1
                continue
            try:
                article = self.client.get_topic_detail(item.topic_id)
                old = self.state.get_article(item.topic_id)
                action = self._needs_export(article, old)
                if action == "skip":
                    summary.skipped_count += 1
                    self.state.set_cursor(item.cursor)
                    continue

                existing_names: set[str] = set()
                if self.config.download_enabled:
                    for idx, att in enumerate(article.attachments):
                        article.attachments[idx] = self.downloader.download(self.config.output_dir, article.topic_id, att, existing_names)
                        self.state.upsert_attachment(article.attachments[idx])
                path = export_article(self.config.output_dir, article)
                if self.config.write_raw:
                    raw = self.config.output_dir / "raw" / f"{article.topic_id}.json"
                    self.client.write_raw(raw, article)
                    article.raw_json_path = raw.relative_to(self.config.output_dir).as_posix()
                self.state.upsert_article(article, path.relative_to(self.config.output_dir).as_posix())
                summary.created_count += int(action == "create")
                summary.updated_count += int(action == "update")
                self.state.set_cursor(item.cursor)
                processed += 1
            except Exception as exc:  # noqa: BLE001
                summary.failed_count += 1
                summary.failures.append({"topic_id": item.topic_id, "error": str(exc)})

        summary_path = self.config.output_dir / "run_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.state.finish_run(summary, str(summary_path))
        return summary

    def rebuild_markdown(self, render_version: str) -> int:
        rows = self.state.conn.execute("SELECT topic_id FROM articles WHERE render_version!=?", (render_version,)).fetchall()
        count = 0
        for row in rows:
            article = self.client.get_topic_detail(int(row["topic_id"]))
            article.render_version = render_version
            path = export_article(self.config.output_dir, article)
            self.state.upsert_article(article, path.relative_to(self.config.output_dir).as_posix())
            count += 1
        return count
