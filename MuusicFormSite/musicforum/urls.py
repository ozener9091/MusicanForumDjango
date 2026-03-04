from django.urls import path, register_converter

from . import views

app_name = "musicforum"

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("categories/", views.categories, name="categories"),
    path("categories/<slug:category_name>", views.category, name="category"),
    path(
        "categories/<slug:category_name>/<int:discussion_id>",
        views.discussion,
        name="discussion",
    ),
]
