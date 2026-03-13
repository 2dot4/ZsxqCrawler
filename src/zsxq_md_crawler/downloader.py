from __future__ import annotations

from pathlib import Path

from .models import Attachment
from .utils.fs import ensure_parent
from .utils.slug import resolve_attachment_name


class AttachmentDownloader:
    def __init__(self, session=None) -> None:
        if session is None:
            import urllib.request

            class _URLLibSession:
                def get(self, url, timeout=60):
                    with urllib.request.urlopen(url, timeout=timeout) as r:
                        class _Resp:
                            def __init__(self, content):
                                self.content = content
                            def raise_for_status(self):
                                return None
                        return _Resp(r.read())
            session = _URLLibSession()
        self.session = session

    def download(self, output_dir: Path, topic_id: int, attachment: Attachment, existing_names: set[str]) -> Attachment:
        name = resolve_attachment_name(attachment.name, attachment.file_id, existing_names)
        rel = Path("attachments") / str(topic_id) / name
        path = output_dir / rel
        ensure_parent(path)
        part = path.with_suffix(path.suffix + ".part")

        if not attachment.download_url:
            attachment.status = "failed"
            attachment.relative_path = rel.as_posix()
            return attachment

        try:
            resp = self.session.get(attachment.download_url, timeout=60)
            resp.raise_for_status()
            with open(part, "wb") as f:
                f.write(resp.content)
            part.replace(path)
            attachment.status = "done"
            attachment.size_bytes = path.stat().st_size
        except Exception:
            attachment.status = "failed"
        attachment.relative_path = rel.as_posix()
        return attachment
