from __future__ import annotations

import argparse

from discussion_cli import (
    add_lookup_arguments,
    category_value,
    get_discussion,
    print_discussion,
    status_value,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update a Discussion record.")
    add_lookup_arguments(parser, required=True)
    parser.add_argument("--title", help="New title.")
    parser.add_argument("--author", help="New author.")
    parser.add_argument("--category", type=category_value, help="New category.")
    parser.add_argument("--status", type=status_value, help="New status.")
    parser.add_argument("--content", help="New content.")
    parser.add_argument("--set-slug", help="New slug.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    updates = {
        "title": args.title,
        "author": args.author,
        "category": args.category,
        "status": args.status,
        "content": args.content,
        "slug": args.set_slug,
    }

    changed_fields = {
        name: value.strip() if isinstance(value, str) else value
        for name, value in updates.items()
        if value is not None
    }
    if not changed_fields:
        parser.error("Provide at least one field to update.")
    for field_name in ("title", "author", "content"):
        if field_name in changed_fields and not changed_fields[field_name]:
            parser.error(f"--{field_name} cannot be empty.")

    discussion = get_discussion(discussion_id=args.id, slug=args.slug)

    for field_name, value in changed_fields.items():
        setattr(discussion, field_name, value)

    discussion.save()

    print("Discussion updated successfully.")
    print_discussion(discussion)


if __name__ == "__main__":
    main()
