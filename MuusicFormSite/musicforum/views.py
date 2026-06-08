import uuid
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, F, Prefetch, Q, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.text import get_valid_filename
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from .forms import CommentForm, DiscussionModelForm, DiscussionSimpleForm, UploadFileForm
from .models import Comment, Discussion, DiscussionReaction, ReactionValue
from .utils import DataMixin


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
        Discussion.objects.select_related("passport", "created_by")
        .prefetch_related(
            Prefetch(
                "comments",
                queryset=Comment.objects.select_related("created_by").order_by("created_at", "id"),
            ),
            "tags",
        )
        .annotate(
            comment_count=Count("comments", distinct=True),
            tag_count=Count("tags", distinct=True),
            like_count=Count(
                "reactions",
                filter=Q(reactions__value=ReactionValue.LIKE),
                distinct=True,
            ),
            dislike_count=Count(
                "reactions",
                filter=Q(reactions__value=ReactionValue.DISLIKE),
                distinct=True,
            ),
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


def _get_initial_category(request):
    category = request.GET.get("category", "").strip()
    valid_categories = {value for value, _ in Discussion.Category.choices}
    return category if category in valid_categories else ""


def _user_display_name(user):
    full_name = (user.get_full_name() or "").strip()
    return full_name or user.get_username()


def _build_discussion_owner(discussion, user):
    discussion.created_by = user
    discussion.author = _user_display_name(user)


def handle_uploaded_file(uploaded_file):
    base_dir = Path(settings.MEDIA_ROOT) / "uploads"
    base_dir.mkdir(parents=True, exist_ok=True)

    source_name = Path(get_valid_filename(uploaded_file.name))
    suffix = source_name.suffix
    random_name = f"{source_name.stem}_{uuid.uuid4().hex}{suffix}"

    with (base_dir / random_name).open("wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)


class DiscussionHomeView(DataMixin, ListView):
    template_name = "musicforum/index.html"
    context_object_name = "discussions"
    title_page = "Главная страница"

    def get_queryset(self):
        self.filters = _build_filters(self.request)
        return _get_discussions(self.filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            **self.filters,
            category_locked=False,
            current_category=self.filters["selected_category"],
        )


class AboutView(LoginRequiredMixin, DataMixin, View):
    template_name = "musicforum/about.html"
    title_page = "О форуме"

    def _get_about_context(self, upload_form):
        annotated_discussions = (
            Discussion.objects.select_related("passport")
            .annotate(
                comment_count=Count("comments", distinct=True),
                like_count=Count(
                    "reactions",
                    filter=Q(reactions__value=ReactionValue.LIKE),
                    distinct=True,
                ),
                dislike_count=Count(
                    "reactions",
                    filter=Q(reactions__value=ReactionValue.DISLIKE),
                    distinct=True,
                ),
                activity_score=Coalesce(F("passport__views_count"), Value(0))
                + Count("comments", distinct=True)
                + Count(
                    "reactions",
                    filter=Q(reactions__value=ReactionValue.LIKE),
                    distinct=True,
                ),
            )
            .order_by("-activity_score", "title")
        )

        top_discussions = annotated_discussions.exclude(status=Discussion.Status.ARCHIVED)[:3]
        orm_status_counts = (
            Discussion.objects.values("status")
            .annotate(total=Count("id"))
            .order_by("status")
        )
        orm_tag_counts = (
            Discussion.objects.values("tags__name")
            .annotate(total=Count("id"))
            .order_by("tags__name")
        )
        orm_reaction_counts = (
            DiscussionReaction.objects.values("value")
            .annotate(total=Count("id"))
            .order_by("value")
        )
        aggregate_stats = annotated_discussions.aggregate(
            average_comments=Avg("comment_count"),
            average_views=Avg("passport__views_count"),
            average_likes=Avg("like_count"),
        )

        return self.get_mixin_context(
            {},
            upload_form=upload_form,
            total_discussions=Discussion.objects.count(),
            published_discussions=Discussion.objects.published().count(),
            active_discussions=Discussion.objects.exclude(status=Discussion.Status.ARCHIVED).count(),
            orm_status_counts=orm_status_counts,
            orm_tag_counts=orm_tag_counts,
            orm_reaction_counts=orm_reaction_counts,
            top_discussions=top_discussions,
            average_comments=aggregate_stats["average_comments"] or 0,
            average_views=aggregate_stats["average_views"] or 0,
            average_likes=aggregate_stats["average_likes"] or 0,
        )

    def get(self, request, *args, **kwargs):
        context = self._get_about_context(UploadFileForm())
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        upload_form = UploadFileForm(request.POST, request.FILES)
        if upload_form.is_valid():
            handle_uploaded_file(upload_form.cleaned_data["file"])
            messages.success(request, "Файл успешно загружен на сервер.")
            return redirect("musicforum:about")

        context = self._get_about_context(upload_form)
        return render(request, self.template_name, context)


class CategoriesView(DataMixin, TemplateView):
    template_name = "musicforum/categories.html"
    title_page = "Категории"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            categories=Discussion.get_category_catalog(),
        )


class DiscussionCategoryView(DataMixin, ListView):
    template_name = "musicforum/category.html"
    context_object_name = "discussions"

    def dispatch(self, request, *args, **kwargs):
        self.current_category_data = Discussion.get_category_data(kwargs["category_slug"])
        if self.current_category_data is None:
            raise Http404("Страница не найдена")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.filters = _build_filters(
            self.request,
            current_category=self.current_category_data["slug"],
        )
        return _get_discussions(self.filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            **self.filters,
            title=self.current_category_data["title"],
            category=self.current_category_data,
            category_locked=True,
            current_category=self.current_category_data["slug"],
        )


class DiscussionDetailView(DataMixin, DetailView):
    model = Discussion
    template_name = "musicforum/discussion.html"
    context_object_name = "discussion"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return _get_discussion_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_reaction = None
        if self.request.user.is_authenticated:
            user_reaction = self.object.reactions.filter(user=self.request.user).first()

        return self.get_mixin_context(
            context,
            title=self.object.title,
            category=Discussion.get_category_data(self.object.category),
            current_category=self.object.category,
            comment_form=CommentForm(),
            can_edit_discussion=self.request.user.is_authenticated
            and (self.request.user.is_staff or self.object.created_by_id == self.request.user.id),
            user_reaction=user_reaction,
        )


class DiscussionToolsView(DataMixin, TemplateView):
    template_name = "musicforum/discussion_tools.html"
    title_page = "Инструменты обсуждений"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            total_discussions=Discussion.objects.count(),
            published_discussions=Discussion.objects.published().count(),
            latest_discussions=_get_discussion_queryset().order_by("-created_at")[:5],
        )


class DiscussionCreateFormView(LoginRequiredMixin, DataMixin, FormView):
    form_class = DiscussionSimpleForm
    template_name = "musicforum/discussion_form.html"
    title_page = "Новая тема (обычная форма)"
    success_url = reverse_lazy("musicforum:index")

    def get_initial(self):
        initial = super().get_initial()
        initial_category = _get_initial_category(self.request)
        if initial_category:
            initial["category"] = initial_category
        return initial

    def form_valid(self, form):
        self.object = Discussion.objects.create(
            title=form.cleaned_data["title"],
            slug=form.cleaned_data["slug"],
            category=form.cleaned_data["category"],
            status=form.cleaned_data["status"],
            content=form.cleaned_data["content"],
            photo=form.cleaned_data["photo"],
            author=_user_display_name(self.request.user),
            created_by=self.request.user,
        )
        self.object.tags.set(form.cleaned_data["tags"])
        messages.success(self.request, "Тема успешно создана через обычную форму.")
        return redirect(self.object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            submit_label="Создать тему",
            form_mode="simple",
        )


class DiscussionCreateSimpleView(DiscussionCreateFormView):
    pass


class DiscussionCreateView(LoginRequiredMixin, DataMixin, CreateView):
    model = Discussion
    form_class = DiscussionModelForm
    template_name = "musicforum/discussion_form.html"
    title_page = "Новая тема"

    def get_initial(self):
        initial = super().get_initial()
        initial_category = _get_initial_category(self.request)
        if initial_category:
            initial["category"] = initial_category
        return initial

    def form_valid(self, form):
        form.instance.author = _user_display_name(self.request.user)
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Тема успешно создана через ModelForm.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            submit_label="Создать тему",
            form_mode="model",
        )


class DiscussionOwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        discussion = self.get_object()
        return self.request.user.is_staff or discussion.created_by_id == self.request.user.id


class DiscussionUpdateView(DiscussionOwnerRequiredMixin, DataMixin, UpdateView):
    model = Discussion
    form_class = DiscussionModelForm
    template_name = "musicforum/discussion_form.html"
    title_page = "Редактирование темы"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def form_valid(self, form):
        form.instance.created_by = self.object.created_by or self.request.user
        form.instance.author = self.object.author or _user_display_name(self.request.user)
        response = super().form_valid(form)
        messages.success(self.request, "Тема успешно обновлена.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            discussion=self.object,
            submit_label="Сохранить изменения",
            form_mode="model",
            current_category=self.object.category,
        )


class DiscussionDeleteView(DiscussionOwnerRequiredMixin, DataMixin, DeleteView):
    model = Discussion
    template_name = "musicforum/discussion_confirm_delete.html"
    context_object_name = "discussion"
    title_page = "Удаление темы"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("musicforum:index")

    def form_valid(self, form):
        messages.success(self.request, "Тема удалена.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(
            context,
            current_category=self.object.category,
        )


class DiscussionCommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        self.discussion = get_object_or_404(Discussion, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.discussion = self.discussion
        form.instance.created_by = self.request.user
        form.instance.author = _user_display_name(self.request.user)
        response = super().form_valid(form)
        messages.success(self.request, "Комментарий добавлен.")
        return response

    def form_invalid(self, form):
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(self.request, error)
        return redirect(f"{self.discussion.get_absolute_url()}#comments")

    def get_success_url(self):
        return f"{self.discussion.get_absolute_url()}#comments"


class DiscussionReactionToggleView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        self.discussion = get_object_or_404(Discussion, slug=kwargs["slug"])
        self.value = kwargs["value"]
        if self.value not in {value for value, _ in ReactionValue.choices}:
            raise Http404("Реакция не найдена")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        reaction, created = DiscussionReaction.objects.get_or_create(
            discussion=self.discussion,
            user=request.user,
            defaults={"value": self.value},
        )

        if not created:
            if reaction.value == self.value:
                reaction.delete()
                messages.success(request, "Реакция удалена.")
            else:
                reaction.value = self.value
                reaction.save(update_fields=["value"])
                messages.success(request, "Реакция обновлена.")
        else:
            messages.success(request, "Реакция сохранена.")

        return redirect(self.discussion.get_absolute_url())
