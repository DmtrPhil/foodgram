from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from .models import User, Subscription


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'recipes_count',
        'subscriptions_count',
    )
    list_display_links = ('id', 'username')
    search_fields = ('email', 'username')
    list_filter = ('is_active', 'is_staff')
    ordering = ('username',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count=Count('recipes'),
            subscriptions_count=Count('subs_on_author')
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, user):
        return user.recipes_count

    @admin.display(description='Подписчиков')
    def subscriptions_count(self, user):
        return user.subscriptions_count


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
