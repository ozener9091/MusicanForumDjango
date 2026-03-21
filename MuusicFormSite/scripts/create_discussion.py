from __future__ import annotations

import argparse

from discussion_cli import Discussion, category_value, print_discussion, status_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Discussion record.")
    parser.add_argument("--title", required=True, help="Discussion title.")
    parser.add_argument("--author", required=True, help="Discussion author.")
    parser.add_argument("--category", required=True, type=category_value, help="Discussion category.")
    parser.add_argument("--content", required=True, help="Discussion content.")
    parser.add_argument(
        "--status",
        default=Discussion.Status.PUBLISHED,
        type=status_value,
        help="Discussion status.",
    )
    parser.add_argument("--slug", default="", help="Optional custom slug.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    title = args.title.strip()
    author = args.author.strip()
    content = args.content.strip()
    slug = args.slug.strip()

    if not title:
        parser.error("--title cannot be empty.")
    if not author:
        parser.error("--author cannot be empty.")
    if not content:
        parser.error("--content cannot be empty.")

    discussion = Discussion.objects.create(
        title=title,
        author=author,
        category=args.category,
        status=args.status,
        content=content,
        slug=slug,
    )

    print("Discussion created successfully.")
    print_discussion(discussion)


if __name__ == "__main__":
    main()
