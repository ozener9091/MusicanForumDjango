from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.utils import timezone
from django.forms import Textarea
from .models import Comment, Discussion, DiscussionPassport, Tag


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "created_at", "comments_count", "is_recent")
    list_filter = ("category", "status", "created_at", "tags")
    search_fields = ("title", "slug", "author", "content", "tags__name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    ordering = ("-created_at",)
    actions = ("publish_selected", "add_featured_tag")

    save_on_top = True
    save_as = True
    fieldsets = (
        ("Основная информация", {"fields": ("title", "slug", "author", "category", "status")}),
        ("Содержание", {"fields": ("content",)}),
        ("Дополнительно", {"fields": ("tags", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at", "updated_at")
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 10, "cols": 70})},
    }

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_comments_count=Count("comments"))

    @admin.display(description="Комментарии", ordering="_comments_count")
    def comments_count(self, obj):
        return obj._comments_count

    @admin.display(description="За 7 дней", boolean=True)
    def is_recent(self, obj):
        return (timezone.now() - obj.created_at).days < 7

    @admin.action(description="Опубликовать выбранные")
    def publish_selected(self, request, queryset):
        updated = queryset.update(status=Discussion.Status.PUBLISHED)
        self.message_user(request, f"Опубликовано: {updated} обсуждений.")

    @admin.action(description="Добавить тег 'Рекомендуемое'")
    def add_featured_tag(self, request, queryset):
        tag, _ = Tag.objects.get_or_create(name="Рекомендуемое")
        for obj in queryset:
            obj.tags.add(tag)
        self.message_user(request, f"Тег добавлен к {queryset.count()} обсуждениям.")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (("Данные тега", {"fields": ("name", "slug")}),)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "discussion", "created_at", "get_preview")
    search_fields = ("author", "text", "discussion__title")
    ordering = ("created_at",)
    fieldsets = (("Комментарий", {"fields": ("discussion", "author", "text", "created_at")}),)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("discussion",)
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 5, "cols": 60})},
    }

    @admin.display(description="Превью текста")
    def get_preview(self, obj):
        return obj.text[:50] + "…" if len(obj.text) > 50 else obj.text


@admin.register(DiscussionPassport)
class DiscussionPassportAdmin(admin.ModelAdmin):
    list_display = ("discussion", "views_count", "bookmarks_count")
    readonly_fields = ("discussion", "views_count", "bookmarks_count")
    fieldsets = (("Статистика", {"fields": ("discussion", "views_count", "bookmarks_count")}),)