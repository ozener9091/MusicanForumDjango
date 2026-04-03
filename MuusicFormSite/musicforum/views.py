from django.contrib import messages
from django.db.models import Avg, Count, F, IntegerField, Prefetch, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.text import slugify

from .data import get_menu
from .models import Comment, Discussion, Tag


def _base_context(current_category=""):
    return {
        "menu": get_menu(),
        "current_category": current_category,
        "category_options": Discussion.Category.choices,
        "status_options": Discussion.get_status_options(),
        "ordering_options": Discussion.get_ordering_options(),
        "all_tags": Tag.objects.order_by("name"),
    }


def _build_filters(request, current_category=""):
    valid_categories = {value for value, _ in Discussion.Category.choices}
    valid_statuses = {value for value, _ in Discussion.get_status_options()}
    valid_orderings = {value for value, _ in Discussion.get_ordering_options()}

    category = current_category or request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()
    ordering = request.GET.get("ordering", "-created_at").strip()
    query = request.GET.get("q", "").strip()

    if category and category not in valid_categories:
        category = ""
    if status and status not in valid_statuses:
        status = ""
    if ordering not in valid_orderings:
        ordering = "-created_at"

    return {
        "selected_category": category,
        "selected_status": status,
        "selected_ordering": ordering,
        "search_query": query,
    }


def _get_discussion_queryset():
    return (
        Discussion.objects.select_related("passport")
        .prefetch_related("tags")
        .annotate(
            comment_count=Count("comments", distinct=True),
            tag_count=Count("tags", distinct=True),
        )
    )


def _get_discussions(filters):
    return (
        _get_discussion_queryset()
        .search(filters["search_query"])
        .for_category(filters["selected_category"])
        .with_status(filters["selected_status"])
        .ordered(filters["selected_ordering"])
    )


def _get_discussion_or_404(slug):
    try:
        return (
            _get_discussion_queryset()
            .prefetch_related(
                Prefetch("comments", queryset=Comment.objects.order_by("created_at", "id"))
            )
            .get(slug=slug)
        )
    except Discussion.DoesNotExist as exc:
        raise Http404("Тема не найдена") from exc


def _parse_tag_ids(source):
    if hasattr(source, "getlist"):
        return [value for value in source.getlist("tags") if value]
    return [str(value) for value in source.get("tags", [])]


def _get_discussion_form_data(source=None, instance=None, initial_category=""):
    source = source or {}
    selected_tags = _parse_tag_ids(source) if source else []
    if not selected_tags and instance is not None:
        selected_tags = [str(tag_id) for tag_id in instance.tags.values_list("id", flat=True)]

    return {
        "title": source.get("title", getattr(instance, "title", "")),
        "slug": source.get("slug", getattr(instance, "slug", "")),
        "author": source.get("author", getattr(instance, "author", "")),
        "category": source.get(
            "category",
            getattr(instance, "category", initial_category or Discussion.Category.GUITAR),
        ),
        "status": source.get(
            "status",
            getattr(instance, "status", Discussion.Status.PUBLISHED),
        ),
        "content": source.get("content", getattr(instance, "content", "")),
        "tags": selected_tags,
    }


def _validate_discussion_form(data):
    valid_categories = {value for value, _ in Discussion.Category.choices}
    valid_statuses = {value for value, _ in Discussion.get_status_options()}
    raw_tag_ids = data.get("tags", [])

    cleaned_data = {
        "title": data.get("title", "").strip(),
        "slug": slugify(data.get("slug", "").strip(), allow_unicode=True),
        "author": data.get("author", "").strip(),
        "category": data.get("category", "").strip(),
        "status": data.get("status", "").strip(),
        "content": data.get("content", "").strip(),
    }
    errors = {}

    if not cleaned_data["title"]:
        errors["title"] = "Введите название темы."
    if not cleaned_data["author"]:
        errors["author"] = "Введите имя автора."
    if cleaned_data["category"] not in valid_categories:
        errors["category"] = "Выберите корректную категорию."
    if cleaned_data["status"] not in valid_statuses:
        errors["status"] = "Выберите корректный статус."
    if not cleaned_data["content"]:
        errors["content"] = "Введите текст темы."

    try:
        tag_ids = [int(value) for value in raw_tag_ids]
    except (TypeError, ValueError):
        tag_ids = []
        errors["tags"] = "Выберите корректные теги."
    else:
        selected_tags = list(Tag.objects.filter(id__in=tag_ids).order_by("name"))
        if len(selected_tags) != len(set(tag_ids)):
            errors["tags"] = "Выберите корректные теги."
        cleaned_data["selected_tags"] = selected_tags

    return cleaned_data, errors


def _save_discussion_tags(discussion_item, selected_tags):
    discussion_item.tags.set(selected_tags)


def index(request):
    filters = _build_filters(request)
    context = {
        **_base_context(),
        **filters,
        "title": "Главная страница",
        "discussions": _get_discussions(filters),
        "category_locked": False,
    }
    return render(request, "musicforum/index.html", context)


def about(request):
    annotated_discussions = (
        Discussion.objects.select_related("passport")
        .annotate(
            comment_count=Count("comments", distinct=True),
            tag_count=Count("tags", distinct=True),
            activity_score=Coalesce(F("passport__views_count"), Value(0))
            + Count("comments", distinct=True)
            + Value(1, output_field=IntegerField()),
        )
        .order_by("-activity_score", "title")
    )

    top_discussions = annotated_discussions.exclude(status=Discussion.Status.ARCHIVED)[:3]
    orm_status_counts = Discussion.objects.values("status").annotate(total=Count("id")).order_by("status")
    orm_tag_counts = (
        Discussion.objects.values("tags__name")
        .annotate(total=Count("id"))
        .order_by("tags__name")
    )
    aggregate_stats = annotated_discussions.aggregate(
        average_comments=Avg("comment_count"),
        average_views=Avg("passport__views_count"),
    )

    context = {
        **_base_context(),
        "title": "О форуме",
        "total_discussions": Discussion.objects.count(),
        "published_discussions": Discussion.objects.published().count(),
        "active_discussions": Discussion.objects.exclude(status=Discussion.Status.ARCHIVED).count(),
        "orm_status_counts": orm_status_counts,
        "orm_tag_counts": orm_tag_counts,
        "top_discussions": top_discussions,
        "average_comments": aggregate_stats["average_comments"] or 0,
        "average_views": aggregate_stats["average_views"] or 0,
    }
    return render(request, "musicforum/about.html", context)


def categories(request):
    context = {
        **_base_context(),
        "title": "Категории",
        "categories": Discussion.get_category_catalog(),
    }
    return render(request, "musicforum/categories.html", context)


def category(request, category_slug):
    current = Discussion.get_category_data(category_slug)
    if current is None:
        raise Http404("Категория не найдена")

    filters = _build_filters(request, current_category=category_slug)
    context = {
        **_base_context(current_category=category_slug),
        **filters,
        "title": current["title"],
        "category": current,
        "discussions": _get_discussions(filters),
        "category_locked": True,
    }
    return render(request, "musicforum/category.html", context)


def discussion(request, slug):
    discussion_item = _get_discussion_or_404(slug)
    context = {
        **_base_context(current_category=discussion_item.category),
        "title": discussion_item.title,
        "discussion": discussion_item,
        "category": Discussion.get_category_data(discussion_item.category),
    }
    return render(request, "musicforum/discussion.html", context)


def discussion_create(request):
    initial_category = request.GET.get("category", "").strip()

    if request.method == "POST":
        form_data = _get_discussion_form_data(request.POST, initial_category=initial_category)
        cleaned_data, form_errors = _validate_discussion_form(form_data)

        if not form_errors:
            discussion_item = Discussion.objects.create(
                title=cleaned_data["title"],
                slug=cleaned_data["slug"],
                author=cleaned_data["author"],
                category=cleaned_data["category"],
                status=cleaned_data["status"],
                content=cleaned_data["content"],
            )
            _save_discussion_tags(discussion_item, cleaned_data["selected_tags"])
            messages.success(request, "Тема успешно создана.")
            return redirect(discussion_item)
    else:
        form_data = _get_discussion_form_data(initial_category=initial_category)
        form_errors = {}

    context = {
        **_base_context(),
        "title": "Новая тема",
        "form_data": form_data,
        "form_errors": form_errors,
        "submit_label": "Создать тему",
    }
    return render(request, "musicforum/discussion_form.html", context)


def discussion_update(request, slug):
    discussion_item = _get_discussion_or_404(slug)

    if request.method == "POST":
        form_data = _get_discussion_form_data(request.POST, instance=discussion_item)
        cleaned_data, form_errors = _validate_discussion_form(form_data)

        if not form_errors:
            discussion_item.title = cleaned_data["title"]
            discussion_item.slug = cleaned_data["slug"]
            discussion_item.author = cleaned_data["author"]
            discussion_item.category = cleaned_data["category"]
            discussion_item.status = cleaned_data["status"]
            discussion_item.content = cleaned_data["content"]
            discussion_item.save()
            _save_discussion_tags(discussion_item, cleaned_data["selected_tags"])
            messages.success(request, "Тема успешно обновлена.")
            return redirect(discussion_item)
    else:
        form_data = _get_discussion_form_data(instance=discussion_item)
        form_errors = {}

    context = {
        **_base_context(current_category=discussion_item.category),
        "title": "Редактирование темы",
        "form_data": form_data,
        "form_errors": form_errors,
        "discussion": discussion_item,
        "submit_label": "Сохранить изменения",
    }
    return render(request, "musicforum/discussion_form.html", context)


def discussion_delete(request, slug):
    discussion_item = _get_discussion_or_404(slug)

    if request.method == "POST":
        discussion_item.delete()
        messages.success(request, "Тема удалена.")
        return redirect("musicforum:index")

    context = {
        **_base_context(current_category=discussion_item.category),
        "title": "Удаление темы",
        "discussion": discussion_item,
    }
    return render(request, "musicforum/discussion_confirm_delete.html", context)
