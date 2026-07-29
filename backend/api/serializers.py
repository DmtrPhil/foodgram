from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from recipes.constants import (
    MAX_COOKING_TIME,
    MIN_COOKING_TIME,
    MIN_VALUE_AMOUNT
)
from users.models import Subscription

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + (
            'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, subscribed):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.subs_user.filter(author=subscribed).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        error_messages={
            'does_not_exist': 'Ингредиент с id {value} не существует.',
        }
    )
    amount = serializers.IntegerField(
        min_value=MIN_VALUE_AMOUNT,
        error_messages={
            'min_value': 'Количество ингредиента должно быть больше {MIN_VALUE_AMOUNT}.',
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
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

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.favorite.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.cart.filter(user=request.user).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
        error_messages={
            'min_value': (
                'Время приготовления не может быть меньше '
                f'{MIN_COOKING_TIME} минуты.'
            ),
            'max_value': (
                'Время приготовления не может превышать '
                f'{MAX_COOKING_TIME} минут.'
            ),
        }
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
            'author',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Ингредиенты обязательны.')
        ingredient_ids = [ingredient['ingredient'].id for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Теги обязательны.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    @staticmethod
    def create_ingredients(ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['ingredient'].id,
                amount=ingredient['amount']
            ) for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.get('ingredients')
        tags = validated_data.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Добавьте хотя бы один ингредиент'}
            )
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Добавьте хотя бы один тег'}
            )
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context=self.context
        ).data


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class SubscriptionListSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True,
        default=0
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, user):
        request = self.context.get('request')
        if not request:
            return []
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = user.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора.'
            )
        return data

    def to_representation(self, instance):
        return SubscriptionListSerializer(
            instance.author,
            context=self.context
        ).data


class BaseFavoriteShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError(
                'Произошла ошибка при добавлении рецепта.'
            )
        recipe = data.get('recipe')
        user = request.user
        model = self.Meta.model
        if model.objects.filter(user=user, recipe=recipe).exists():
            model_name = model._meta.verbose_name
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {model_name}.'
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe).data


class FavoriteSerializer(BaseFavoriteShoppingCartSerializer):

    class Meta(BaseFavoriteShoppingCartSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseFavoriteShoppingCartSerializer):

    class Meta(BaseFavoriteShoppingCartSerializer.Meta):
        model = Cart
