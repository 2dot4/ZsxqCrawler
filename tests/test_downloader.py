from pathlib import Path
import tempfile
import unittest

from zsxq_md_crawler.downloader import AttachmentDownloader
from zsxq_md_crawler.models import Attachment


class _Resp:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None


class _Session:
    def __init__(self):
        self.count = 0

    def get(self, url, timeout=60):
        self.count += 1
        return _Resp(b"abc")


class TestDownloader(unittest.TestCase):
    def test_atomic_and_conflict_name(self):
        with tempfile.TemporaryDirectory() as td:
            d = AttachmentDownloader(session=_Session())
            existing = set()
            a1 = Attachment("id1", 1, "报告.pdf", download_url="http://x")
            a2 = Attachment("id2", 1, "报告.pdf", download_url="http://x")
            r1 = d.download(Path(td), 1, a1, existing)
            r2 = d.download(Path(td), 1, a2, existing)
            self.assertEqual(r1.status, "done")
            self.assertIn("__id2", r2.relative_path)
            self.assertTrue((Path(td) / r1.relative_path).exists())


if __name__ == "__main__":
    unittest.main()
