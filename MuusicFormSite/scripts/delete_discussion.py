from __future__ import annotations

import argparse

from discussion_cli import add_lookup_arguments, get_discussion


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Delete a Discussion record.")
    add_lookup_arguments(parser, required=True)
    parser.add_argument("--yes", action="store_true", help="Delete without confirmation.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    discussion = get_discussion(discussion_id=args.id, slug=args.slug)
    discussion_id = discussion.id
    discussion_title = discussion.title

    if not args.yes:
        answer = input(f"Delete discussion '{discussion_title}' (id={discussion_id})? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Deletion cancelled.")
            return

    discussion.delete()
    print(f"Discussion id={discussion_id} deleted successfully.")


if __name__ == "__main__":
    main()
