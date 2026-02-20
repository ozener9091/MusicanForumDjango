from . import views, converter
from django.urls import path, register_converter


app_name = 'musicforum'
register_converter(converter.FourDigitYearConverter,"year4")

urlpatterns = [
    path('categories/', views.categories, name='categories'),
    path('categories/<slug:category_name>', views.category, name='category'),
    path('categories/<slug:category_name>/<int:discussion_id>', views.discussion, name='discussion'),
    path('test/<year4:year>', views.test, name='test'),
    path('', views.index, name='index'),
]