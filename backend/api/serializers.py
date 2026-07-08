from rest_framework import serializers
from django.contrib.auth import get_user_model

from recipes.validators import validator_cooking_time
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class RecipeIngredientCreateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    
    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )
    
    def validate_cooking_time(self, value):
        validator_cooking_time(value)
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = self.create_recipe(validated_data)
        self.add_tags(recipe, tags)
        self.add_ingredients(recipe, ingredients)

        return recipe

    def create_recipe(self, validated_data):
        return Recipe.objects.create(
            author =  self.context['request'].user,
            **validated_data
        )
    
    def add_tags(self, recipe, tags):
        recipe.tags.set(tags)
    
    def add_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shoping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shoping_cart'
        )
    
    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')

