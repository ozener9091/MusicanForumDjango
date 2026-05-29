from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView

from .forms import LoginUserForm, ProfileUserForm, RegisterUserForm, UserPasswordChangeForm


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy('musicforum:index')


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Регистрация'}
    success_url = reverse_lazy('users:login')


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {
        'title': 'Профиль пользователя',
        'default_image': settings.DEFAULT_USER_IMAGE,
    }

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('users:profile')


class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_form.html'
    extra_context = {'title': 'Изменение пароля'}


class LogoutUser(LogoutView):
    http_method_names = ['get', 'post', 'options']
    next_page = reverse_lazy('musicforum:index')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ToggleSocialAuthStatus(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'users.social_auth'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        request.user.social_auth_verified = not request.user.social_auth_verified
        request.user.save(update_fields=['social_auth_verified'])

        if request.user.social_auth_verified:
            messages.success(request, 'Статус social auth: подтвержден.')
        else:
            messages.success(request, 'Статус social auth: отключен.')

        return redirect('users:profile')
