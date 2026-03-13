from pathlib import Path
import tempfile
import unittest

from zsxq_md_crawler.models import Article, Attachment, Cursor, RunSummary
from zsxq_md_crawler.state_store import StateStore


class TestStateStore(unittest.TestCase):
    def test_init_upsert_and_run(self):
        with tempfile.TemporaryDirectory() as td:
            s = StateStore(Path(td) / "state.db")
            s.init()
            s.set_cursor(Cursor("2026", 1))
            self.assertEqual(s.get_cursor().topic_id, 1)
            art = Article(1, 1, 1, "t", "a", "c", "m", "a", "u", None, "md", "x", None, "v2", [])
            s.upsert_article(art, "articles/1.md")
            self.assertIsNotNone(s.get_article(1))
            att = Attachment("f", 1, "n", relative_path="attachments/1/n", status="done")
            s.upsert_attachment(att)
            summary = RunSummary(run_id="r", mode="incremental")
            s.begin_run("r", "incremental")
            s.finish_run(summary, "output/run_summary.json")
            s.close()


if __name__ == "__main__":
    unittest.main()
