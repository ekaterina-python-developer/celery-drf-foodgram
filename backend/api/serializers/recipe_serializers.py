from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.serializers.user_serializers import UserProfileSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    author = UserProfileSerializer(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField(required=True, use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, ingredients_data):
        """Проверяет корректность списка ингредиентов."""
        if not ingredients_data:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.')

        ingredient_ids = [item['id'] for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')

        for item in ingredients_data:
            amount = item.get('amount')
            if amount is None or int(amount) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0.'
                )

        return ingredients_data

    def to_representation(self, instance):
        """Формирует представление рецепта."""
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags, many=True).data
        representation['ingredients'] = RecipeIngredientSerializer(
            instance.recipes.all(), many=True
        ).data
        return representation

    def to_internal_value(self, data):
        """Преобразует внешние данные во внутренние."""
        internal_value = super().to_internal_value(data)
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        internal_value['tags'] = tags
        internal_value['ingredients'] = ingredients
        return internal_value

    def create_and_update_recipe_ingredients(self, recipe, ingredients):
        """Создает или обновляет ингредиенты рецепта."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=int(ingredient['amount']),
            )
            for ingredient in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        """Создает новый рецепт."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = super().create({
            **validated_data,
            'author': self.context['request'].user
        })

        recipe.tags.set(tags)
        self.create_and_update_recipe_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_and_update_recipe_ingredients(instance, ingredients)
        return super().update(instance, validated_data)


class BaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного и корзины покупок."""

    class Meta:
        fields = ('user', 'recipe')

    def __init__(self, *args, **kwargs):
        """Добавляет валидатор уникальности для пары (user, recipe)."""
        super().__init__(*args, **kwargs)
        model = getattr(self.Meta, 'model', None)
        if model:
            self.Meta.validators = [
                UniqueTogetherValidator(
                    queryset=model.objects.all(),
                    fields=('user', 'recipe'),
                    message='Этот рецепт уже добавлен.'
                )
            ]


class FavoriteSerializer(BaseSerializer):
    """Сериализатор для избранного."""

    class Meta(BaseSerializer.Meta):
        model = Favorite


class ShoppingListSerializer(BaseSerializer):
    """Сериализатор для корзины покупок."""

    class Meta(BaseSerializer.Meta):
        model = ShoppingList
