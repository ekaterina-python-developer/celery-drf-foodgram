from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для рецептов."""

    image = Base64ImageField(required=True, use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
