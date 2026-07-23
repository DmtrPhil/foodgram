import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from .constants import (
    MAX_LENGTH_MEASUREMENT_UNIT,
    MAX_NAME_LENGTH,
    MAX_NAME_LENGTH_INGREDIENTS,
    MAX_NAME_LENGTH_TAG,
    MAX_SHORT_LINK_LENGTH,
    MAX_SLUG_LENGTH_TAG,
    MAX_STR_LENGTH,
)
from .validators import validator_cooking_time, validator_image_size

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH_TAG,
        verbose_name='Название',
        unique=True
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH_TAG,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:MAX_STR_LENGTH]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH_INGREDIENTS,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEASUREMENT_UNIT,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name[:MAX_STR_LENGTH]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes'
    )
    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение',
        validators=[validator_image_size]
    )
    text = models.TextField('Текст')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(validator_cooking_time,),
        verbose_name='Время приготовления (в минутах)'
    )
    short_link = models.CharField(
        max_length=MAX_SHORT_LINK_LENGTH,
        unique=True,
        blank=True,
        verbose_name='Короткая ссылка'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def clean(self):
        if not self.recipe_ingredients.exists():
            raise ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.'
            )

    def generate_short_link(self):
        return uuid.uuid4().hex[:MAX_SHORT_LINK_LENGTH]

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name[:MAX_STR_LENGTH]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        verbose_name='Ингридиент',
        related_name='recipe_ingredients'
    )
    amount = models.PositiveIntegerField('Количество')

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'

    def __str__(self):
        return f'{
            self.ingredient.name
        } - {self.amount} {self.ingredient.measurement_unit}'


class UserRecipeModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeModel):

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'),
        )


class Cart(UserRecipeModel):

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_cart'),
        )
