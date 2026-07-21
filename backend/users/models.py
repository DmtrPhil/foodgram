from django.contrib.auth.models import AbstractUser
from django.db import models
from recipes.constants import (
    MAX_EMAIL_LENGHT,
    MAX_FIRST_NAME_LENGHT,
    MAX_LAST_NAME_LENGT,
    MAX_STR_LENGTH,
    MAX_USERNAME_LENGHT,
)
from recipes.validators import validator_image_size

from .validators import username_validator


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'
    ROLES = (
        (USER, 'Пользователь'),
        (ADMIN, 'Администратор'),
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGHT,
        unique=True,
        verbose_name='Эл. почта'
    )
    username = models.CharField(
        max_length=MAX_USERNAME_LENGHT,
        unique=True,
        verbose_name='Username',
        validators=(username_validator,)
    )
    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LENGHT,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LENGT,
        verbose_name='Фамилия'
    )
    role = models.CharField(
        max_length=max(len(key) for key, _ in ROLES),
        choices=ROLES,
        default=USER,
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар',
        validators=[validator_image_size]
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:MAX_STR_LENGTH]

    @property
    def is_admin(self):
        return self.is_superuser or self.role == self.ADMIN
