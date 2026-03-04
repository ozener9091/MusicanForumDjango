from django import template

from musicforum.data import get_categories

register = template.Library()


@register.simple_tag
def forum_name():
    return "Music Forum"


@register.inclusion_tag("musicforum/includes/category_list.html")
def show_categories(selected_slug=""):
    return {
        "categories": get_categories(),
        "selected_slug": selected_slug,
    }
