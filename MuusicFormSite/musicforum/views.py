from django.contrib import messages
from django.db import connection
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .data import get_menu
from .models import Discussion


def _base_context(current_category=""):
    return {
        "menu": get_menu(),
        "current_category": current_category,
        "category_options": Discussion.Category.choices,
        "status_options": Discussion.get_status_options(),
        "ordering_options": Discussion.get_ordering_options(),
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


def _get_discussions(filters):
    return (
        Discussion.objects.search(filters["search_query"])
        .for_category(filters["selected_category"])
        .with_status(filters["selected_status"])
        .ordered(filters["selected_ordering"])
    )


def _get_sql_statistics():
    table_name = Discussion._meta.db_table

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT status, COUNT(*)
            FROM {table_name}
            GROUP BY status
            ORDER BY status
            """
        )
        status_counts = dict(cursor.fetchall())

        cursor.execute(
            f"""
            SELECT category, COUNT(*)
            FROM {table_name}
            GROUP BY category
            ORDER BY category
            """
        )
        category_counts = dict(cursor.fetchall())

    return {
        "status_counts": status_counts,
        "category_counts": category_counts,
    }


def _get_discussion_form_data(source=None, instance=None, initial_category=""):
    source = source or {}
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
    }


def _validate_discussion_form(data):
    valid_categories = {value for value, _ in Discussion.Category.choices}
    valid_statuses = {value for value, _ in Discussion.get_status_options()}

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

    return cleaned_data, errors


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
    sql_statistics = _get_sql_statistics()
    context = {
        **_base_context(),
        "title": "О форуме",
        "total_discussions": Discussion.objects.count(),
        "published_discussions": Discussion.objects.published().count(),
        "sql_status_counts": sql_statistics["status_counts"],
        "sql_category_counts": sql_statistics["category_counts"],
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
    discussion_item = get_object_or_404(Discussion, slug=slug)
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
            discussion_item = Discussion.objects.create(**cleaned_data)
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
    discussion_item = get_object_or_404(Discussion, slug=slug)

    if request.method == "POST":
        form_data = _get_discussion_form_data(request.POST, instance=discussion_item)
        cleaned_data, form_errors = _validate_discussion_form(form_data)

        if not form_errors:
            for field_name, value in cleaned_data.items():
                setattr(discussion_item, field_name, value)
            discussion_item.save()
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
    discussion_item = get_object_or_404(Discussion, slug=slug)

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
