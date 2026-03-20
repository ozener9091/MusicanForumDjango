from django.http import HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render


def page_not_found(request, exception):
    return HttpResponseNotFound("Страница не найдена: 404")


def error_on_server(request):
    return HttpResponseServerError("Ошибка на сервере: 500")
