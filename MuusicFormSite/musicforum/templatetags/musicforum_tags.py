from django import template
from django.db.models import Count

from musicforum.models import Discussion, Tag

register = template.Library()


@register.simple_tag
def forum_name():
    return "Форум для музыкантов"


@register.simple_tag
def published_discussions_total():
    return Discussion.objects.published().count()


@register.inclusion_tag("musicforum/includes/category_list.html")
def show_categories(selected_slug=""):
    return {
        "categories": Discussion.get_category_catalog(),
        "selected_slug": selected_slug,
    }


@register.inclusion_tag("musicforum/includes/popular_tags.html")
def show_popular_tags(limit=5):
    return {
        "popular_tags": Tag.objects.annotate(total=Count("discussions", distinct=True))
        .filter(total__gt=0)
        .order_by("-total", "name")[:limit]
    }
