from pathlib import Path
import tempfile
import unittest

from zsxq_md_crawler.config import AppConfig
from zsxq_md_crawler.models import Article, Attachment, TopicListItem
from zsxq_md_crawler.state_store import StateStore
from zsxq_md_crawler.sync import SyncService


class FakeClient:
    def __init__(self):
        self.calls = []

    def list_column_topics(self, column_id, limit=20):
        return [
            TopicListItem(topic_id=1, attached_to_column_time="2026-01-01T00:00:00+08:00", modified_at="m1"),
            TopicListItem(topic_id=2, attached_to_column_time="2026-01-01T00:00:00+08:00", modified_at="m1"),
        ]

    def get_topic_detail(self, topic_id):
        self.calls.append(topic_id)
        return Article(topic_id, 1, 1, f"t{topic_id}", "a", "2026-01-01", "m1", "2026-01-01T00:00:00+08:00", "u", "<p>x</p>", "x", str(topic_id), None, "v2", [Attachment("f", topic_id, "a.txt", download_url=None)])

    def write_raw(self, path, article):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")


class TestSyncCursor(unittest.TestCase):
    def test_tie_break_and_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = AppConfig(cookie="c", group_id=1, column_id=1, output_dir=Path(td), write_raw=False)
            state = StateStore(Path(td) / "state.db")
            state.init()
            client = FakeClient()
            svc = SyncService(client, cfg, state)
            s1 = svc.crawl(mode="incremental")
            self.assertEqual(s1.created_count, 2)
            s2 = svc.crawl(mode="incremental")
            self.assertEqual(s2.created_count + s2.updated_count, 0)
            self.assertGreaterEqual(s2.skipped_count, 2)
            state.close()


if __name__ == "__main__":
    unittest.main()
