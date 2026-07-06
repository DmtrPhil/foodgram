from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import filters, mixins, status, viewsets

from recipes.models import Recipe

User = get_user_model()

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()