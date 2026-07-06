from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    #is_favorite = 
    #is_in_shopping_cart = 
    author = filters.CharFilter(field_name='author__id')
    tags = filters.CharFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorite', 'is_in_shopping_cart')