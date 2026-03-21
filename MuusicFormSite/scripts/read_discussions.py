from __future__ import annotations

import argparse

from discussion_cli import (
    Discussion,
    add_lookup_arguments,
    category_value,
    get_discussion,
    ordering_value,
    print_discussion,
    print_discussion_list,
    status_value,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read Discussion records.")
    add_lookup_arguments(parser, required=False)
    parser.add_argument("--category", type=category_value, help="Filter by category.")
    parser.add_argument("--status", type=status_value, help="Filter by status.")
    parser.add_argument("--query", help="Search in title, content or author.")
    parser.add_argument(
        "--ordering",
        default="-created_at",
        type=ordering_value,
        help="Sort order.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Number of records to show.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.id is not None or args.slug:
        discussion = get_discussion(discussion_id=args.id, slug=args.slug)
        print_discussion(discussion)
        return

    discussions = (
        Discussion.objects.search((args.query or "").strip())
        .for_category(args.category or "")
        .with_status(args.status or "")
        .ordered(args.ordering)
    )

    limit = args.limit if args.limit > 0 else 20
    print_discussion_list(list(discussions[:limit]))


if __name__ == "__main__":
    main()
