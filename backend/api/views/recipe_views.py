import datetime
from io import BytesIO

from django.db.models import F, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsOwnerOrAdminOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeSerializer, ShoppingListSerializer,
                             TagSerializer)
from backend.mixins import CreateDeleteMixin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)


class BaseReadOnlyViewSet(ModelViewSet):
    """Базовый ViewSet без пагинации."""

    pagination_class = None


class RecipeViewSet(CreateDeleteMixin, ModelViewSet):
    """ViewSet для рецептов с дополнительными действиями."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsOwnerOrAdminOrReadOnly, IsAuthenticatedOrReadOnly)
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        """Оптимизированный queryset с предзагрузкой связанных данных."""
        user = self.request.user
        return (
            Recipe.objects.with_flags(user)
            .select_related('author')
            .prefetch_related('tags', 'recipes__ingredient')
        )

    @staticmethod
    def generate_pdf(user):
        """Генерирует PDF файл со списком покупок."""
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        ingredients = (
            RecipeIngredient.objects.filter(recipe__shoppinglist__user=user)
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('amount'))
        )
        buffer = BytesIO()
        page = canvas.Canvas(buffer, pagesize=letter)
        text = page.beginText(70, 750)
        text.setFont('STSong-Light', 14)

        if not ingredients:
            text.textLine('Список покупок пуст.')
        else:
            for ing in ingredients:
                name = ing.get('name', 'Неизвестный ингредиент')
                unit = ing.get('unit', '')
                total = ing.get('total_amount', 0)
                text.textLine(f'{name} ({unit}) — {total}')

        page.drawText(text)
        page.showPage()
        page.save()
        buffer.seek(0)
        return buffer

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_url = request.build_absolute_uri(
            reverse('short-link', args=[recipe.pk])
        )
        return Response({'short-link': short_url})

    @action(detail=True, methods=('post',))
    def favorite(self, request, pk):
        """Добавить рецепт в избранное."""
        favorite_data = {'user': request.user.id, 'recipe': pk}
        return self.create_item(
            Favorite, FavoriteSerializer, favorite_data, request)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        """Удалить рецепт из избранного."""
        return self.delete_item(Favorite, user=request.user, recipe=pk)

    @action(
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок в формате PDF."""
        time_format = '%d/%m - %H:%M'
        formatted_datetime = datetime.datetime.now().strftime(time_format)

        pdf = self.generate_pdf(request.user)

        return FileResponse(
            pdf,
            as_attachment=True,
            filename=f'Список покупок от {formatted_datetime}.pdf'
        )

    @action(detail=True, methods=('post',), url_path='shopping_cart')
    def add_to_cart(self, request, pk):
        """Добавить рецепт в корзину покупок."""
        cart_data = {'user': request.user.id, 'recipe': pk}
        return self.create_item(
            ShoppingList, ShoppingListSerializer, cart_data, request)

    @add_to_cart.mapping.delete
    def remove_from_cart(self, request, pk):
        """Удалить рецепт из корзины покупок."""
        return self.delete_item(ShoppingList, user=request.user, recipe=pk)


def short_link_redirect(request, pk):
    """Перенаправляет с короткой ссылки на страницу рецепта."""
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect('recipes-detail', pk=recipe.pk)


class IngredientViewSet(BaseReadOnlyViewSet):
    """ViewSet для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class TagViewSet(BaseReadOnlyViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
