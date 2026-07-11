from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from recipes.validators import validator_cooking_time
from recipes.models import (
    Cart, Favorite, Ingredient, Recipe, RecipeIngredient, Tag, Subscription, User
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )
    
    def get_is_subscribed(self, subscribed):
        user = self.context.get('request').user
        if user and user.is_authenticated and user != subscribed:
            return Subscription.objects.filter(user=user, author=subscribed).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Этот email уже занят.')
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Этот username уже занят.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    

class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный пароль')
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, self.context['request'].user)
        except ValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('name', 'slug')

class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


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
    
    def get_ingredients(self, object):
        ingredients = RecipeIngredient.objects.filter(recipe=object)
        return [
            {
                'id': ingredient.ingredient.id,
                'name': ingredient.ingredient.name,
                'measurement_unit': ingredient.ingredient.measurement_unit,
                'amount': ingredient.amount
            }
            for ingredient in ingredients
        ]
    
    def get_is_favorited(self, object):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=object).exists()
        return False

    def get_is_in_shoping_cart(self, object):
        user = self.context['request'].user
        if user.is_authenticated:
            return Cart.objects.filter(user=user, recipe=object).exists()
        return False


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class SubscriptionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()


    class Meta:
        model = Subscription
        fields = ('author', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, subscription):
        return True

    def get_recipes(self, subscription):
        recipes_limit = self.context.get('recipes_limit')
        recipes = subscription.author.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, subscription):
        return subscription.author.recipes.count()
