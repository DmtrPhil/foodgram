from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError

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
        'is_staff'
    )
    list_display_links = ('id', 'username')
    search_fields = ('email', 'username')
    list_filter = ('is_active', 'is_staff')
    ordering = ('username',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')

    def save_model(self, request, subscription, form, change):
        if subscription.user == subscription.author:
            raise ValidationError("Нельзя подписаться на себя.")
        super().save_model(request, subscription, form, change)
