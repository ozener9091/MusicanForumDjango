from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError


def page_not_found(request, exception):
    return HttpResponseNotFound("Страница не найдена 404")


def error_on_server(request):
    return HttpResponseServerError("Ошибка на сервере 500")

