from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe


def short_link_redirect(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f'/recipes/{recipe.id}/')
