from __future__ import annotations

from pathlib import Path

from .models import Article
from .utils.fs import atomic_write_text


def article_markdown_path(output_dir: Path, article: Article) -> Path:
    year, month = "unknown", "00"
    if article.created_at and len(article.created_at) >= 7:
        year = article.created_at[0:4]
        month = article.created_at[5:7]
    return output_dir / "articles" / year / month / f"{article.topic_id}.md"


def _yaml_escape(value: str | None) -> str:
    if value is None:
        return '""'
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_markdown(article: Article) -> str:
    lines = [
        "---",
        f"topic_id: {article.topic_id}",
        f"column_id: {article.column_id}",
        f"group_id: {article.group_id}",
        f"title: {_yaml_escape(article.title)}",
        f"author: {_yaml_escape(article.author_name)}",
        f"created_at: {_yaml_escape(article.created_at)}",
        f"modified_at: {_yaml_escape(article.modified_at)}",
        f"attached_to_column_time: {_yaml_escape(article.attached_to_column_time)}",
        f"source_url: {_yaml_escape(article.source_url)}",
        f"render_version: {_yaml_escape(article.render_version)}",
        f"attachments_count: {len(article.attachments)}",
        "---",
        "",
        f"# {article.title or f'话题 {article.topic_id}'}",
        "",
        (article.body_markdown or "").strip(),
        "",
    ]

    attachment_lines: list[str] = []
    seen: set[str] = set()
    for a in article.attachments:
        if a.relative_path and a.relative_path not in seen:
            seen.add(a.relative_path)
            attachment_lines.append(f"- [{a.name}]({a.relative_path})")
    if attachment_lines:
        lines.extend(["## 附件", "", *attachment_lines, ""])
    return "\n".join(lines).rstrip() + "\n"


def export_article(output_dir: Path, article: Article) -> Path:
    path = article_markdown_path(output_dir, article)
    atomic_write_text(path, render_markdown(article))
    return path
