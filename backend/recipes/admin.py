from django.contrib import admin
from django.contrib.admin import register

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)

admin.site.register(Favorite)
admin.site.register(ShoppingList)


class BaseAdmin(admin.ModelAdmin):
    """Базовый админ-класс с общими настройками."""

    search_fields = ('name',)
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    """Inline для ингредиентов рецепта в админке."""

    model = RecipeIngredient
    extra = 1


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель для модели Recipe."""

    list_display = ('id', 'name', 'author', 'cooking_time', 'favorites_count')
    search_fields = ('name', 'author')
    list_filter = ('author', 'name')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='Счётчик избранного')
    def favorites_count(self, recipe):
        """Количество добавлений рецепта в избранное."""
        return recipe.favorite.count()


@register(Ingredient)
class IngredientAdmin(BaseAdmin):
    """Админ-панель для модели Ingredient."""

    list_display = ('id', 'name', 'measurement_unit')


@register(Tag)
class TagAdmin(BaseAdmin):
    """Админ-панель для модели Tag."""

    list_display = ('id', 'name', 'color', 'slug')


@register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-панель для модели RecipeIngredient."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')
