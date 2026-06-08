from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    photo = models.ImageField(
        upload_to='users/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Фотография',
    )
    date_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата рождения',
    )
    social_auth_verified = models.BooleanField(
        default=False,
        verbose_name='Социальная авторизация подтверждена',
    )

    class Meta:
        permissions = [
            ('social_auth', 'Можно авторизоваться через социальные сети'),
        ]
