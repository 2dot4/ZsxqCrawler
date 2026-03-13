from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import Article, Attachment, Cursor, RunSummary


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def init(self) -> None:
        self.conn.executescript(
            """
CREATE TABLE IF NOT EXISTS sync_state (key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS articles (
    topic_id INTEGER PRIMARY KEY,column_id INTEGER NOT NULL,group_id INTEGER NOT NULL,title TEXT,author_name TEXT,
    created_at TEXT,modified_at TEXT,attached_to_column_time TEXT,source_url TEXT,markdown_path TEXT NOT NULL,
    raw_json_path TEXT,content_checksum TEXT NOT NULL,render_version TEXT NOT NULL,last_synced_at TEXT NOT NULL,is_deleted INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS attachments (
    file_id TEXT PRIMARY KEY,topic_id INTEGER NOT NULL,name TEXT NOT NULL,ext TEXT,size_bytes INTEGER,mime_type TEXT,
    checksum TEXT,relative_path TEXT NOT NULL,status TEXT NOT NULL,last_error TEXT,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,mode TEXT NOT NULL,started_at TEXT NOT NULL,finished_at TEXT,scanned_count INTEGER NOT NULL DEFAULT 0,
    created_count INTEGER NOT NULL DEFAULT 0,updated_count INTEGER NOT NULL DEFAULT 0,skipped_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,summary_path TEXT);
"""
        )
        self.conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_cursor(self) -> Cursor | None:
        cur = self.conn.execute("SELECT key,value FROM sync_state WHERE key IN (?,?)", (
            "list_cursor_attached_to_column_time", "list_cursor_topic_id"))
        rows = {r["key"]: r["value"] for r in cur.fetchall()}
        if "list_cursor_attached_to_column_time" not in rows or "list_cursor_topic_id" not in rows:
            return None
        return Cursor(rows["list_cursor_attached_to_column_time"], int(rows["list_cursor_topic_id"]))

    def set_cursor(self, cursor: Cursor) -> None:
        now = self._now()
        self.conn.execute("REPLACE INTO sync_state(key,value,updated_at) VALUES(?,?,?)", (
            "list_cursor_attached_to_column_time", cursor.attached_to_column_time, now))
        self.conn.execute("REPLACE INTO sync_state(key,value,updated_at) VALUES(?,?,?)", (
            "list_cursor_topic_id", str(cursor.topic_id), now))
        self.conn.commit()

    def get_article(self, topic_id: int):
        return self.conn.execute("SELECT * FROM articles WHERE topic_id=?", (topic_id,)).fetchone()

    def upsert_article(self, article: Article, markdown_path: str) -> None:
        self.conn.execute(
            """REPLACE INTO articles(topic_id,column_id,group_id,title,author_name,created_at,modified_at,
            attached_to_column_time,source_url,markdown_path,raw_json_path,content_checksum,render_version,last_synced_at,is_deleted)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
            (article.topic_id, article.column_id, article.group_id, article.title, article.author_name, article.created_at,
             article.modified_at, article.attached_to_column_time, article.source_url, markdown_path, article.raw_json_path,
             article.content_checksum, article.render_version, self._now()),
        )
        self.conn.commit()

    def upsert_attachment(self, att: Attachment, last_error: str | None = None) -> None:
        self.conn.execute(
            """REPLACE INTO attachments(file_id,topic_id,name,ext,size_bytes,mime_type,checksum,relative_path,status,last_error,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (att.file_id, att.topic_id, att.name, att.ext, att.size_bytes, att.mime_type, att.checksum,
             att.relative_path or "", att.status, last_error, self._now()),
        )
        self.conn.commit()

    def begin_run(self, run_id: str, mode: str) -> None:
        self.conn.execute("REPLACE INTO runs(run_id,mode,started_at) VALUES(?,?,?)", (run_id, mode, self._now()))
        self.conn.commit()

    def finish_run(self, summary: RunSummary, summary_path: str) -> None:
        self.conn.execute(
            """UPDATE runs SET finished_at=?,scanned_count=?,created_count=?,updated_count=?,skipped_count=?,failed_count=?,summary_path=?
            WHERE run_id=?""",
            (self._now(), summary.scanned_count, summary.created_count, summary.updated_count, summary.skipped_count,
             summary.failed_count, summary_path, summary.run_id),
        )
        self.conn.commit()
