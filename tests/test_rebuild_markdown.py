from pathlib import Path
import tempfile
import unittest

from zsxq_md_crawler.config import AppConfig
from zsxq_md_crawler.models import Article, TopicListItem
from zsxq_md_crawler.state_store import StateStore
from zsxq_md_crawler.sync import SyncService


class _Client:
    def list_column_topics(self, column_id, limit=20):
        return [TopicListItem(1, "2026-01-01T00:00:00+08:00", "m")]

    def get_topic_detail(self, topic_id):
        return Article(topic_id, 1, 1, "t", "a", "2026-01-01", "m", "2026-01-01T00:00:00+08:00", "u", "", "body", "cc", None, "v1", [])

    def write_raw(self, path, article):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")


class TestRebuild(unittest.TestCase):
    def test_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = AppConfig(cookie="", group_id=1, column_id=1, output_dir=Path(td), write_raw=False)
            s = StateStore(Path(td) / "state.db")
            s.init()
            client = _Client()
            svc = SyncService(client, cfg, s)
            svc.crawl(mode="full")
            changed = svc.rebuild_markdown("v2")
            self.assertEqual(changed, 1)
            row = s.get_article(1)
            self.assertEqual(row["render_version"], "v2")
            self.assertEqual(row["markdown_path"], "articles/2026/01/1.md")
            s.close()


if __name__ == "__main__":
    unittest.main()
