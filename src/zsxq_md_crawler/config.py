from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


@dataclass
class AppConfig:
    cookie: str
    group_id: int
    column_id: int
    output_dir: Path
    write_raw: bool = True
    page_size: int = 20
    max_retries: int = 3
    download_enabled: bool = True
    download_retry_times: int = 3
    render_version: str = "v2"


def load_config(path: str | Path) -> AppConfig:
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    cookie = os.getenv("ZSXQ_COOKIE") or raw.get("auth", {}).get("cookie", "")
    target = raw.get("target", {})
    output = raw.get("output", {})
    sync = raw.get("sync", {})
    download = raw.get("download", {})
    render = raw.get("render", {})

    return AppConfig(
        cookie=cookie,
        group_id=int(target.get("group_id", 0)),
        column_id=int(target.get("column_id", 0)),
        output_dir=Path(output.get("dir", "./output")),
        write_raw=bool(output.get("write_raw", True)),
        page_size=int(sync.get("page_size", 20)),
        max_retries=int(sync.get("max_retries", 3)),
        download_enabled=bool(download.get("enabled", True)),
        download_retry_times=int(download.get("retry_times", 3)),
        render_version=str(render.get("version", "v2")),
    )
