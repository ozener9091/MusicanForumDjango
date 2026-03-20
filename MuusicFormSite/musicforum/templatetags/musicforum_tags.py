from django import template

from musicforum.models import Discussion

register = template.Library()


@register.simple_tag
def forum_name():
    return "Форум для музыкантов"


@register.inclusion_tag("musicforum/includes/category_list.html")
def show_categories(selected_slug=""):
    return {
        "categories": Discussion.get_category_catalog(),
        "selected_slug": selected_slug,
    }
