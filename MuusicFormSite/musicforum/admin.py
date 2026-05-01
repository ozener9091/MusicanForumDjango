from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Comment, Discussion, DiscussionPassport, Tag


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    fields = (
        "title",
        "slug",
        "author",
        "category",
        "status",
        "content",
        "photo",
        "post_photo",
        "tags",
    )
    readonly_fields = ("post_photo",)
    list_display = ("title", "post_photo", "author", "category", "status", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    ordering = ("-created_at",)

    @admin.display(description="Изображение")
    def post_photo(self, discussion: Discussion):
        if discussion.photo:
            return mark_safe(f"<img src='{discussion.photo.url}' width='50'>")
        return "Без фото"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "discussion", "created_at")
    ordering = ("created_at",)


@admin.register(DiscussionPassport)
class DiscussionPassportAdmin(admin.ModelAdmin):
    list_display = ("discussion", "views_count", "bookmarks_count")
