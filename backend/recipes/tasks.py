from celery import shared_task
from django.db.models import F, Sum
from recipes.models import RecipeIngredient


@shared_task
def generate_shopping_list_text(user_id):
    """Генерации списка покупок."""
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
    return content