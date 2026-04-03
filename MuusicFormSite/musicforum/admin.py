from django.contrib import admin

from .models import Comment, Discussion, DiscussionPassport, Tag


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "created_at")
    list_filter = ("category", "status", "created_at", "tags")
    search_fields = ("title", "slug", "author", "content", "tags__name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    ordering = ("-created_at",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "discussion", "created_at")
    search_fields = ("author", "text", "discussion__title")
    ordering = ("created_at",)


@admin.register(DiscussionPassport)
class DiscussionPassportAdmin(admin.ModelAdmin):
    list_display = ("discussion", "views_count", "bookmarks_count")
