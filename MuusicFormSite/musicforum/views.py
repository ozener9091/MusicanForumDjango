from django.shortcuts import render, redirect
from django.http import HttpResponse


def index(request):
    return HttpResponse("Главная страница сайта")


def categories(request):
    if request.GET:
        print(f"Данные из запроса:{request.GET}")
    return HttpResponse("Страница с категориями форума")


def category(request, category_name):
    if request.GET:
        print(f"Данные из запроса:{request.GET}")
    return HttpResponse("Страница категории " + category_name)


def discussion(request, category_name, discussion_id):
    if request.GET:
        print(f"Данные из запроса:{request.GET}")
    if discussion_id <= 0:
        return redirect('musicforum:index')
    return HttpResponse(f"Обсуждение #{discussion_id} из категории {category_name}")


def test(request, year):
    if year >=2026:
        return redirect('musicforum:index')
    return HttpResponse(f"Год:{year}")