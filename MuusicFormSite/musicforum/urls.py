from django.urls import path
from django.contrib import admin

from . import views

app_name = "musicforum"


urlpatterns = [
    path("", views.DiscussionHomeView.as_view(), name="index"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("categories/", views.CategoriesView.as_view(), name="categories"),
    path("categories/<slug:category_slug>/", views.DiscussionCategoryView.as_view(), name="category"),
    path("discussions/tools/", views.DiscussionToolsView.as_view(), name="discussion_tools"),
    path("discussions/create/form/", views.DiscussionCreateFormView.as_view(), name="discussion_create_form"),
    path("discussions/create/simple/", views.DiscussionCreateSimpleView.as_view(), name="discussion_create_simple"),
    path("discussions/create/", views.DiscussionCreateView.as_view(), name="discussion_create"),
    path("discussions/<str:slug>/", views.DiscussionDetailView.as_view(), name="discussion"),
    path("discussions/<str:slug>/edit/", views.DiscussionUpdateView.as_view(), name="discussion_update"),
    path("discussions/<str:slug>/delete/", views.DiscussionDeleteView.as_view(), name="discussion_delete"),
]

admin.site.site_header = "Панель администрирования"
admin.site.site_title = "Музыкальный форум - Администрирование"
admin.site.index_title = "Добро пожаловать в панель администрирования Музыкального форума"
