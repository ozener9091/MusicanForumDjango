from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, Discussion, DiscussionPassport, DiscussionReaction, Tag


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    fields = (
        "title",
        "slug",
        "author",
        "created_by",
        "category",
        "status",
        "content",
        "photo",
        "post_photo",
        "tags",
    )
    readonly_fields = ("post_photo",)
    list_display = (
        "title",
        "post_photo",
        "author",
        "created_by",
        "category",
        "status",
        "created_at",
    )
    list_filter = ("category", "status", "created_at")
    search_fields = ("title", "author", "content", "created_by__username")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    ordering = ("-created_at",)

    @admin.display(description="Изображение")
    def post_photo(self, discussion: Discussion):
        if discussion.photo:
            return format_html("<img src='{}' width='50' alt='{}'>", discussion.photo.url, discussion.title)
        return "Без фото"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("display_author", "discussion", "created_at")
    search_fields = ("author", "text", "discussion__title", "created_by__username")
    ordering = ("created_at",)

    @admin.display(description="Автор")
    def display_author(self, obj: Comment):
        return obj.display_author


@admin.register(DiscussionPassport)
class DiscussionPassportAdmin(admin.ModelAdmin):
    list_display = ("discussion", "views_count", "bookmarks_count")


@admin.register(DiscussionReaction)
class DiscussionReactionAdmin(admin.ModelAdmin):
    list_display = ("discussion", "user", "value", "created_at")
    list_filter = ("value", "created_at")
    search_fields = ("discussion__title", "user__username")
