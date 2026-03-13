from __future__ import annotations

import argparse

from .client import ZsxqClient
from .config import load_config
from .state_store import StateStore
from .sync import SyncService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zsxq-md")
    parser.add_argument("--config", default="config.toml")
    sub = parser.add_subparsers(dest="command", required=True)

    crawl = sub.add_parser("crawl")
    crawl.add_argument("--column-id", type=int)
    mode = crawl.add_mutually_exclusive_group(required=True)
    mode.add_argument("--full", action="store_true")
    mode.add_argument("--incremental", action="store_true")
    crawl.add_argument("--max-items", type=int)

    export = sub.add_parser("export")
    export.add_argument("--topic-id", type=int, required=True)

    download = sub.add_parser("download")
    download.add_argument("--topic-id", type=int, required=True)

    sub.add_parser("verify")
    rebuild = sub.add_parser("rebuild-markdown")
    rebuild.add_argument("--render-version", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if getattr(args, "column_id", None):
        config.column_id = args.column_id

    state = StateStore(config.output_dir / "state.db")
    state.init()
    client = ZsxqClient(config.cookie, config.group_id, render_version=config.render_version)
    service = SyncService(client=client, config=config, state=state)

    try:
        if args.command == "crawl":
            mode = "full" if args.full else "incremental"
            service.crawl(mode=mode, max_items=args.max_items)
        elif args.command == "export":
            article = client.get_topic_detail(args.topic_id)
            from .exporter import export_article

            export_article(config.output_dir, article)
        elif args.command == "download":
            article = client.get_topic_detail(args.topic_id)
            existing: set[str] = set()
            for att in article.attachments:
                service.downloader.download(config.output_dir, args.topic_id, att, existing)
        elif args.command == "verify":
            print("state db:", state.db_path)
        elif args.command == "rebuild-markdown":
            service.rebuild_markdown(args.render_version)
    finally:
        state.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
