import uuid
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.db.models import Avg, Count, F, IntegerField, Prefetch, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import redirect, render

from .data import get_menu
from .forms import DiscussionModelForm, DiscussionSimpleForm, UploadFileForm
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


def _get_initial_category(request):
    category = request.GET.get("category", "").strip()
    valid_categories = {value for value, _ in Discussion.Category.choices}
    return category if category in valid_categories else ""


def handle_uploaded_file(uploaded_file):
    base_dir = Path(settings.MEDIA_ROOT) / "uploads"
    base_dir.mkdir(parents=True, exist_ok=True)

    source_name = Path(uploaded_file.name)
    suffix = source_name.suffix
    random_name = f"{source_name.stem}_{uuid.uuid4().hex}{suffix}"

    with (base_dir / random_name).open("wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)


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
    if request.method == "POST":
        upload_form = UploadFileForm(request.POST, request.FILES)
        if upload_form.is_valid():
            handle_uploaded_file(upload_form.cleaned_data["file"])
            messages.success(request, "Файл успешно загружен на сервер.")
            return redirect("musicforum:about")
    else:
        upload_form = UploadFileForm()

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
        "upload_form": upload_form,
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


def discussion_create_simple(request):
    initial = {}
    initial_category = _get_initial_category(request)
    if initial_category:
        initial["category"] = initial_category

    if request.method == "POST":
        form = DiscussionSimpleForm(request.POST)
        if form.is_valid():
            discussion_item = Discussion.objects.create(
                title=form.cleaned_data["title"],
                slug=form.cleaned_data["slug"],
                author=form.cleaned_data["author"],
                category=form.cleaned_data["category"],
                status=form.cleaned_data["status"],
                content=form.cleaned_data["content"],
            )
            discussion_item.tags.set(form.cleaned_data["tags"])
            messages.success(request, "Тема успешно создана через обычную форму.")
            return redirect(discussion_item)
    else:
        form = DiscussionSimpleForm(initial=initial)

    context = {
        **_base_context(),
        "title": "Новая тема (обычная форма)",
        "form": form,
        "submit_label": "Создать тему",
        "form_mode": "simple",
    }
    return render(request, "musicforum/discussion_form.html", context)


def discussion_create(request):
    initial = {}
    initial_category = _get_initial_category(request)
    if initial_category:
        initial["category"] = initial_category

    if request.method == "POST":
        form = DiscussionModelForm(request.POST, request.FILES)
        if form.is_valid():
            discussion_item = form.save()
            messages.success(request, "Тема успешно создана через ModelForm.")
            return redirect(discussion_item)
    else:
        form = DiscussionModelForm(initial=initial)

    context = {
        **_base_context(),
        "title": "Новая тема",
        "form": form,
        "submit_label": "Создать тему",
        "form_mode": "model",
    }
    return render(request, "musicforum/discussion_form.html", context)


def discussion_update(request, slug):
    discussion_item = _get_discussion_or_404(slug)

    if request.method == "POST":
        form = DiscussionModelForm(request.POST, request.FILES, instance=discussion_item)
        if form.is_valid():
            discussion_item = form.save()
            messages.success(request, "Тема успешно обновлена.")
            return redirect(discussion_item)
    else:
        form = DiscussionModelForm(instance=discussion_item)

    context = {
        **_base_context(current_category=discussion_item.category),
        "title": "Редактирование темы",
        "form": form,
        "discussion": discussion_item,
        "submit_label": "Сохранить изменения",
        "form_mode": "model",
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
