import unittest

from zsxq_md_crawler.utils.slug import safe_filename


class TestFilenamePolicy(unittest.TestCase):
    def test_invalid_long_and_chinese(self):
        self.assertEqual(safe_filename('a/b:c*?"<>|.txt'), "a_b_c______.txt")
        self.assertTrue(len(safe_filename("x" * 300 + ".txt")) <= 128)
        self.assertEqual(safe_filename("中文文件名.pdf"), "中文文件名.pdf")


if __name__ == "__main__":
    unittest.main()
