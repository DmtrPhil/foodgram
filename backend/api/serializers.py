import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer
)
from recipes.models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
)
from recipes.validators import (
    validator_cooking_time,
    validator_ingredients,
    validator_tags,
)
from rest_framework import serializers

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class CustomUserCreateSerializer(DjoserUserCreateSerializer):

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class CustomUserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, subscribed):
        user = self.context.get('request').user
        if user and user.is_authenticated and user != subscribed:
            return Subscription.objects.filter(
                user=user, author=subscribed
            ).exists()
        return False


class CustomSetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True, validators=(validate_password,)
    )
    current_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def create(self, validated_data):
        recipe = self.context.get('recipe')
        ingredient_id = validated_data.get('id')
        amount = validated_data.get('amount')
        ingredient = Ingredient.objects.get(id=ingredient_id)
        return RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            amount=amount
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
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
            'ingredients',
        )

    def validate_cooking_time(self, value):
        validator_cooking_time(value)
        return value

    def validate(self, data):
        if 'ingredients' in data:
            ingredients = data.get('ingredients', [])
            validator_ingredients(ingredients)
            ingredient_ids = [item['id'] for item in ingredients]
            existing_ids = set(
                Ingredient.objects.filter(id__in=ingredient_ids)
                .values_list('id', flat=True)
            )
            for ingredient_id in ingredient_ids:
                if ingredient_id not in existing_ids:
                    raise serializers.ValidationError(
                        f'Ингредиент с id {ingredient_id} не существует'
                    )
        elif not self.instance:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент'
            )
        if 'tags' in data:
            tags = data.get('tags', [])
            validator_tags(tags)
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        for ingredient_data in ingredients_data:
            ingredient_serializer = RecipeIngredientCreateSerializer(
                data=ingredient_data,
                context={
                    'recipe': recipe,
                    'request': self.context.get('request')
                }
            )
            ingredient_serializer.is_valid(raise_exception=True)
            ingredient_serializer.save(recipe=recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in validated_data:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно'}
            )
        if 'tags' not in validated_data:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно'}
            )
        if 'ingredients' in validated_data:
            ingredients = validated_data.get('ingredients', [])
            if not ingredients:
                raise serializers.ValidationError(
                    {'ingredients': 'Добавьте хотя бы один ингредиент'}
                )
        for attr, value in validated_data.items():
            if attr not in ('tags', 'ingredients'):
                setattr(instance, attr, value)
        instance.save()
        if 'tags' in validated_data:
            instance.tags.set(validated_data['tags'])
        if 'ingredients' in validated_data:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in validated_data['ingredients']:
                ingredient = Ingredient.objects.get(id=ingredient_data['id'])
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
        return instance

    def create_recipe(self, validated_data):
        return Recipe.objects.create(
            author=self.context['request'].user,
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
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
            'is_in_shopping_cart'
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

    def get_is_in_shopping_cart(self, object):
        user = self.context['request'].user
        if user.is_authenticated:
            return Cart.objects.filter(user=user, recipe=object).exists()
        return False


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

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
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, subscription):
        return True

    def get_recipes(self, user):
        recipes_limit = self.context.get('recipes_limit')
        recipes = user.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, user):
        return user.recipes.count()
