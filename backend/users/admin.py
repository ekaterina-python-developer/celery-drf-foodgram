from django.contrib import admin
from django.contrib.admin import register

from users.models import Subscription, User


@register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель для пользователей."""

    def save_model(self, request, obj, form, change):
        """Сохраняет модель с хешированием пароля."""
        if obj.pk:
            orig_obj = User.objects.get(pk=obj.pk)
            if obj.password != orig_obj.password:
                obj.set_password(obj.password)
        else:
            obj.set_password(obj.password)

        obj.save()

    list_display = (
        'id',
        'is_active',
        'username',
        'email',
    )
    search_fields = ('username', 'email')
    list_filter = (
        'is_active',
        'last_name',
        'email',
    )


@register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для подписок."""

    list_display = ('follower', 'following')
    search_fields = ('follower', 'following')
    list_filter = ('follower', 'following')
    empty_value_display = '-пусто-'
