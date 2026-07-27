import uuid
from io import StringIO

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponsePermanentRedirect, FileResponse
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter
from recipes.models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from .serializers import (
    AvatarSerializer,
    FavoriteShoppingCartSerializer,
    UserSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    RecipeMinifiedSerializer,
    SubscriptionListSerializer,
    SubscriptionCreateSerializer,
    TagSerializer,
)
from users.models import Subscription

User = get_user_model()


def short_link_redirect(request, short_link):
    try:
        recipe = Recipe.objects.get(short_link=short_link)
        path = f'/recipes/{recipe.id}/'
    except Recipe.DoesNotExist:
        path = '/not_found'
    redirect_url = request.build_absolute_uri(path)
    return HttpResponsePermanentRedirect(redirect_url)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'subscriptions':
            queryset = queryset.annotate(recipes_count=Count('recipes'))
        return queryset

    @action(detail=False, methods=('get',))
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context=self.context
        )
        return Response(serializer.data)

    @action(detail=True, methods=('post',))
    def subscribe(self, request, pk=None):
        author = self.get_object()
        serializer = SubscriptionCreateSerializer(
            data={'user': request.user.id, 'author': author.id},
            context=self.context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionListSerializer(
                author,
                context=self.context
            ).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = self.get_object()
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Вы не подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionListSerializer(
            page,
            many=True,
            context=self.context
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=('put',), url_path='me/avatar')
    def avatar(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context=self.context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': request.user.avatar.url},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'tags',
        'ingredients'
    )

    @staticmethod
    def format_shopping_list(ingredients):
        return '\r\n'.join(
            f'{name} — {data["amount"]} {data["unit"]}'
            for name, data in ingredients.items()
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_to_collection(self, request, pk, model, serializer_class):
        recipe = self.get_object()
        serializer = serializer_class(
            data={'recipe': recipe.id},
            context={
                'request': request,
                'recipe': recipe,
                'model': model
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeMinifiedSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self.add_to_collection(
            request,
            pk,
            Favorite,
            FavoriteShoppingCartSerializer
        )

    @favorite.mapping.delete
    @permission_classes((IsAuthenticated,))
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self.add_to_collection(
            request,
            pk,
            Cart,
            FavoriteShoppingCartSerializer
        )

    @shopping_cart.mapping.delete
    @permission_classes((IsAuthenticated,))
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        deleted, _ = Cart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Рецепта нет в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',))
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        content = self.format_shopping_list(ingredients)
        file = StringIO(content)
        response = FileResponse(
            file,
            content_type='text/plain; charset=utf-8'
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = uuid.uuid4().hex[:8]
            recipe.save()
        short_link = request.build_absolute_uri(
            reverse('short-link-redirect', args=(recipe.short_link,))
        )
        return Response({'short-link': short_link})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    pagination_class = None
