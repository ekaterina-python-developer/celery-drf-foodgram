from django.apps import apps
from django.db import models
from django.db.models import BooleanField, Exists, OuterRef, Value


class RecipeQuerySet(models.QuerySet):
    """QuerySet для рецептов с флагами избранного и корзины."""

    def with_flags(self, user):
        """Добавляет флаги избранного и корзины к рецептам."""
        Favorite = apps.get_model('recipes', 'Favorite')
        ShoppingList = apps.get_model('recipes', 'ShoppingList')

        if not user.is_authenticated:
            return self.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField()),
            )

        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(recipe=OuterRef('pk'), user=user)
            ),
            is_in_shopping_cart=Exists(
                ShoppingList.objects.filter(recipe=OuterRef('pk'), user=user)
            ),
        )
