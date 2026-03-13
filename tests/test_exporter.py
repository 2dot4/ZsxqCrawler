import unittest

from zsxq_md_crawler.exporter import render_markdown
from zsxq_md_crawler.models import Article, Attachment
from zsxq_md_crawler.utils.html_to_md import html_to_markdown


class TestExporter(unittest.TestCase):
    def test_html_convert_and_frontmatter_escape(self):
        md = html_to_markdown('<p>Hello</p><ul><li>A</li></ul><blockquote>Q</blockquote><pre><code>x=1</code></pre><a href="https://a">link</a>')
        art = Article(1, 2, 3, 'ti"tle', "au", "2026-01-01", "2026-01-02", "2026-01-03", "https://s", None, md, "c", None, "v2", [Attachment("f1", 1, "a.pdf", relative_path="../attachments/1/a.pdf")])
        out = render_markdown(art)
        self.assertIn('title: "ti\\"tle"', out)
        self.assertIn("## 附件", out)
        self.assertIn("- [a.pdf](../attachments/1/a.pdf)", out)


if __name__ == "__main__":
    unittest.main()
