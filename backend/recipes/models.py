from django.contrib.auth import get_user_model
from django.db import models

from .validators import validator_cooking_time

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    slug = models.SlugField(max_length=20, verbose_name='Слаг')


class Ingredient(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=20,
        verbose_name='Единица измерения'
    )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(
        upload_to='api/images/',
        verbose_name='Изображение'
    )
    text = models.TextField('Текст')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    tags = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(validator_cooking_time,),
        verbose_name='Время приготовления (в минутах)'

    )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент'
    )
    amount = models.PositiveIntegerField('Количество')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='Рецепт'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'),
        )