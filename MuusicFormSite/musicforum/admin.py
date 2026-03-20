from django.contrib import admin

from .models import Discussion


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "created_at")
    list_filter = ("category", "status", "created_at")
    search_fields = ("title", "slug", "author", "content")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)
