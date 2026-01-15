import logging

from celery import shared_task
from django.core.cache import cache
from django.db.models import F, Sum

from recipes.models import RecipeIngredient

logger = logging.getLogger(__name__)


@shared_task
def generate_shopping_list_text(user_id):
    """Генерируем список покупок И КЭШИРУЕМ его."""
    cache_key = f'shopping_list_user_{user_id}'
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    ingredients = (
        RecipeIngredient.objects.filter(recipe__shoppinglist__user_id=user_id)
        .values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('name')
    )
    lines = []
    for ing in ingredients:
        line = f"{ing['name']} ({ing['unit']}) — {ing['total_amount']}"
        lines.append(line)

    content = "\n".join(lines) if lines else "Список покупок пуст"
    cache.set(cache_key, content, timeout=300)
    return content
