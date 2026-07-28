from django.contrib import admin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['amount'].required = True
        return formset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'display_tags',
        'display_ingredients',
        'image_preview',
        'favorites_count'
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author')
    readonly_fields = ('short_link',)
    list_select_related = ('author',)
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            favorites_count=Count('favorite')
        )

    @admin.display(description='Теги')
    def display_tags(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, obj):
        return ', '.join(
            recipe_ingredient.ingredient.name
            for recipe_ingredient in obj.recipe_ingredients.all()
        )

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        return mark_safe(
            f'<img src="{obj.image.url}" width="80" height="60" />'
        )

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites_count


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
