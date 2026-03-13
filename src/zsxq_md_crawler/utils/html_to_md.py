from __future__ import annotations

from html.parser import HTMLParser


class _SimpleHTMLToMD(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self.stack: list[str] = []
        self.href: str | None = None
        self.pre_depth = 0

    def handle_starttag(self, tag: str, attrs):
        self.stack.append(tag)
        attrs_dict = dict(attrs)
        if tag == "p":
            if self.out and not self.out[-1].endswith("\n\n"):
                self.out.append("\n\n")
        elif tag in {"ul", "ol"}:
            self.out.append("\n")
        elif tag == "li":
            self.out.append("- ")
        elif tag == "blockquote":
            self.out.append("\n> ")
        elif tag == "pre":
            self.pre_depth += 1
            self.out.append("\n```\n")
        elif tag == "code" and self.pre_depth == 0:
            self.out.append("`")
        elif tag == "a":
            self.href = attrs_dict.get("href")
            self.out.append("[")

    def handle_endtag(self, tag: str):
        if tag == "li":
            self.out.append("\n")
        elif tag == "blockquote":
            self.out.append("\n")
        elif tag == "pre":
            self.pre_depth = max(self.pre_depth - 1, 0)
            self.out.append("\n```\n")
        elif tag == "code" and self.pre_depth == 0:
            self.out.append("`")
        elif tag == "a":
            url = self.href or ""
            self.out.append(f"]({url})")
            self.href = None
        if self.stack:
            self.stack.pop()

    def handle_data(self, data: str):
        self.out.append(data)


def html_to_markdown(html: str | None) -> str:
    if not html:
        return ""
    parser = _SimpleHTMLToMD()
    parser.feed(html)
    text = "".join(parser.out)
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip() + "\n"
