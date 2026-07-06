from rest_framework import serializers
from django.contrib.auth import get_user_model

from recipes.validators import validator_cooking_time
from recipes.models import Recipe

User = get_user_model()

class RecipeSerializer(serializers.ModelSerializer):
    

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

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_cooking_time(self, value):
        validator_cooking_time(value)
        return value