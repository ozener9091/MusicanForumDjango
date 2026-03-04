from django.http import Http404
from django.shortcuts import redirect, render

from .data import (
    get_categories,
    get_category,
    get_discussion,
    get_discussions,
    get_menu,
)


def index(request):
    context = {
        "title": "главная страница",
        "menu": get_menu(),
        "current_category": "",
        "discussions": get_discussions(),
    }
    return render(request, "musicforum/index.html", context)


def about(request):
    context = {
        "title": "о форуме",
        "menu": get_menu(),
        "current_category": "",
    }
    return render(request, "musicforum/about.html", context)


def categories(request):
    context = {
        "title": "категории",
        "menu": get_menu(),
        "current_category": "",
        "categories": get_categories(),
    }
    return render(request, "musicforum/categories.html", context)


def category(request, category_name):
    current = get_category(category_name)
    if current is None:
        raise Http404("Категория не найдена")

    context = {
        "title": current["title"],
        "menu": get_menu(),
        "current_category": current["slug"],
        "category": current,
        "discussions": get_discussions(category_name),
    }
    return render(request, "musicforum/category.html", context)


def discussion(request, category_name, discussion_id):
    if discussion_id <= 0:
        return redirect("musicforum:index")

    current = get_category(category_name)
    discussion_item = get_discussion(category_name, discussion_id)
    if current is None or discussion_item is None:
        raise Http404("Обсуждение не найдено")

    context = {
        "title": discussion_item["title"],
        "menu": get_menu(),
        "current_category": current["slug"],
        "category": current,
        "discussion": discussion_item,
    }
    return render(request, "musicforum/discussion.html", context)
