from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import django


PROJECT_DIR = Path(__file__).resolve().parents[1]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MuusicFormSite.settings")
django.setup()

from musicforum.models import Discussion


CATEGORY_CHOICES = dict(Discussion.Category.choices)
STATUS_CHOICES = dict(Discussion.Status.choices)
ORDERING_CHOICES = {value for value, _ in Discussion.get_ordering_options()}


def category_value(value: str) -> str:
    return _validate_choice(value, CATEGORY_CHOICES, "category")


def status_value(value: str) -> str:
    return _validate_choice(value, STATUS_CHOICES, "status")


def ordering_value(value: str) -> str:
    if value not in ORDERING_CHOICES:
        raise argparse.ArgumentTypeError(
            f"Unsupported ordering '{value}'. Allowed values: {', '.join(sorted(ORDERING_CHOICES))}"
        )
    return value


def add_lookup_arguments(parser: argparse.ArgumentParser, *, required: bool) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument("--id", type=int, help="Discussion ID.")
    group.add_argument("--slug", help="Discussion slug.")


def get_discussion(*, discussion_id: int | None = None, slug: str | None = None) -> Discussion:
    lookup = {"id": discussion_id} if discussion_id is not None else {"slug": slug}

    try:
        return Discussion.objects.get(**lookup)
    except Discussion.DoesNotExist as exc:
        target = f"id={discussion_id}" if discussion_id is not None else f"slug={slug}"
        raise SystemExit(f"Discussion not found for {target}.") from exc


def print_discussion(discussion: Discussion) -> None:
    print(f"id: {discussion.id}")
    print(f"title: {discussion.title}")
    print(f"slug: {discussion.slug}")
    print(f"author: {discussion.author}")
    print(f"category: {discussion.category} ({CATEGORY_CHOICES.get(discussion.category, 'unknown')})")
    print(f"status: {discussion.status} ({STATUS_CHOICES.get(discussion.status, 'unknown')})")
    print(f"created_at: {discussion.created_at.isoformat()}")
    print(f"updated_at: {discussion.updated_at.isoformat()}")
    print("content:")
    print(discussion.content)


def print_discussion_list(discussions) -> None:
    if not discussions:
        print("No discussions found.")
        return

    for discussion in discussions:
        print(
            f"[{discussion.id}] {discussion.title} | slug={discussion.slug} | "
            f"author={discussion.author} | category={discussion.category} | status={discussion.status}"
        )


def _validate_choice(value: str, choices: dict[str, str], field_name: str) -> str:
    if value not in choices:
        raise argparse.ArgumentTypeError(
            f"Unsupported {field_name} '{value}'. Allowed values: {', '.join(sorted(choices))}"
        )
    return value
