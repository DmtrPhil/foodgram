import uuid
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    SAFE_METHODS
)

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    CustomUserSerializer,
    CustomUserCreateSerializer,
    CustomSetPasswordSerializer,
    RecipeListSerializer,
    RecipeCreateSerializer,
    RecipeMinifiedSerializer,
    SubscriptionSerializer,
    TagSerializer,
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

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return (AllowAny(),)
        if self.action in (
            'subscribe',
            'unsubscribe',
            'subscriptions',
            'set_password',
            'avatar',
            'me',
        ):
            return (IsAuthenticated(),)
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        return (IsAdmin(),)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=('get', 'put', 'patch'))
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=('post',))
    def set_password(self, request):
        serializer = CustomSetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        author = self.get_object()
        if author == request.user:
            return Response(
                {'error': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(
            user=request.user, author=author
        ).exists():
            return Response(
                {'error': 'Вы уже подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(
            user=request.user,
            author=author
        )
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = SubscriptionSerializer(
            author,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = self.get_object()
        subscription = Subscription.objects.filter(
            user=request.user,
            author=author
        )
        if not subscription.exists():
            return Response(
                {'error': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(user=request.user)
        authors = [sub.author for sub in subscriptions]
        recipes_limit = request.query_params.get('recipes_limit')
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=('put', 'delete'), url_path='me/avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            if 'avatar' not in request.FILES and 'avatar' not in request.data:
                return Response(
                    {'error': 'Файл не передан'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'avatar' in request.FILES:
                request.user.avatar = request.FILES['avatar']
            else:
                from api.serializers import Base64ImageField
                request.user.avatar = Base64ImageField().to_internal_value(
                    request.data['avatar']
                )
            request.user.save()
            return Response(
                {'avatar': request.user.avatar.url},
                status=status.HTTP_200_OK
            )
        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeListSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeListSerializer

    def get_permissions(self):
        if self.action in ('get_link', 'list', 'retrieve'):
            return (AllowAny(),)
        if self.action in ('update', 'partial_update', 'destroy'):
            return (IsAuthorOrReadOnly(),)
        return (IsAuthenticated(),)

    def create(self, request, *args, **kwargs):
        serializer = RecipeCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        response_serializer = RecipeListSerializer(
            recipe,
            context={'request': request}
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = RecipeCreateSerializer(
            instance,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        response_serializer = RecipeListSerializer(
            recipe,
            context={'request': request}
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'error': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if Cart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Cart.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        cart = Cart.objects.filter(user=request.user, recipe=recipe)
        if not cart.exists():
            return Response(
                {'error': 'Рецепта нет в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response(
                {'error': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = {}
        for cart_item in cart_items:
            recipe_ingredients = RecipeIngredient.objects.filter(
                recipe=cart_item.recipe
            )
            for recipe_ingredient in recipe_ingredients:
                name = recipe_ingredient.ingredient.name
                if name not in ingredients:
                    ingredients[name] = {
                        'amount': 0,
                        'unit': recipe_ingredient.ingredient.measurement_unit
                    }
                ingredients[name]['amount'] += recipe_ingredient.amount
        content = '\n'.join(
            f'{name} — {data['amount']} {data['unit']}'
            for name, data in ingredients.items()
        )
        response = Response(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = uuid.uuid4().hex[:8]
            recipe.save()
        short_link = request.build_absolute_uri(f'/s/{recipe.short_link}/')
        return Response({'short-link': short_link})


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

    def check_permissions(self, request):
        if request.method not in SAFE_METHODS:
            if not request.user.is_authenticated or not request.user.is_staff:
                raise MethodNotAllowed(request.method)
        super().check_permissions(request)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    pagination_class = None

    def check_permissions(self, request):
        if request.method not in SAFE_METHODS:
            if not request.user.is_authenticated or not request.user.is_staff:
                raise MethodNotAllowed(request.method)
        super().check_permissions(request)
