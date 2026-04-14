from django.urls import path
from django.contrib import admin

from . import views

app_name = "musicforum"


urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("categories/", views.categories, name="categories"),
    path("categories/<slug:category_slug>/", views.category, name="category"),
    path("discussions/create/", views.discussion_create, name="discussion_create"),
    path("discussions/<str:slug>/", views.discussion, name="discussion"),
    path("discussions/<str:slug>/edit/", views.discussion_update, name="discussion_update"),
    path("discussions/<str:slug>/delete/", views.discussion_delete, name="discussion_delete"),
]

admin.site.site_header = "Панель администрирования"
admin.site.site_title = "Музыкальный форум - Администрирование"
admin.site.index_title = "Добро пожаловать в панель администрирования Музыкального форума"
