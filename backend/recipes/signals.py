import logging

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ShoppingList

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ShoppingList)
@receiver(post_delete, sender=ShoppingList)
def invalidate_shopping_cache(sender, instance, **kwargs):
    user_id = instance.user_id
    cache_key = f'shopping_list_user_{user_id}'
    cache.delete(cache_key)
