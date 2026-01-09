import string

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.serializers.short_serializers import ShortRecipeSerializer
from users.models import Subscription

User = get_user_model()


class UserProfileSerializer(UserSerializer):
    """Сериализатор пользователя с подпиской и аватаром."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, author):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return (
            user
            and user.is_authenticated
            and user.subscriptions.filter(following=author).exists()
        )

    def get_avatar(self, obj):
        """Возвращает URL аватара."""
        return obj.avatar.url if obj.avatar else None


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления и удаления аватара пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, attrs):
        """Проверка перед обновлением/удалением аватара."""
        avatar = attrs.get('avatar', None)
        if avatar is None and not self.instance.avatar:
            raise ValidationError('Аватар не установлен, нечего удалять.')
        return attrs

    def update(self, instance, validated_data):
        """Обновляет или удаляет аватар пользователя."""
        data = validated_data.copy()
        avatar = data.get('avatar')
        if avatar is None:
            instance.avatar.delete(save=False)
            data['avatar'] = None
        return super().update(instance, data)

    def to_representation(self, instance):
        """Возвращает URL аватара."""
        return {'avatar': instance.avatar.url if instance.avatar else None}


class UserSubscriptionSerializer(UserProfileSerializer):
    """Сериализатор подписки с рецептами пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserProfileSerializer.Meta):        
        fields = UserProfileSerializer.Meta.fields + ( # type: ignore[assignment]
            'recipes',
            'recipes_count',
        )

    def validate_limit(self, value):
        """Проверяет, что limit — положительное целое число."""
        if value is None:
            return None

        str_value = str(value)
        if not set(str_value) <= set(string.digits):
            raise serializers.ValidationError(
                {'limit': 'Параметр "limit" должен содержать только цифры.'}
            )

        value = int(str_value)
        if value < 0:
            raise serializers.ValidationError(
                {'limit': 'Параметр "limit" должен быть положительным числом.'}
            )

        return value

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя с ограничением по количеству."""
        request = self.context.get('request')
        limit = request.query_params.get('limit')
        limit = self.validate_limit(limit)
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:limit]
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context
        ).data


class UnsubscribeSerializer(serializers.Serializer):
    """Сериализатор для проверки корректности отписки."""

    following_id = serializers.IntegerField()

    def validate(self, attrs):
        """Проверяет, что пользователь действительно подписан."""
        follower = self.context['request'].user
        following_id = attrs['following_id']

        if not follower.subscriptions.filter(
                following_id=following_id).exists():
            raise ValidationError('Вы не подписаны на этого пользователя.')

        return attrs


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на пользователей."""

    class Meta:
        model = Subscription
        fields = (
            'follower',
            'following',
        )

    def validate(self, attrs):
        """Проверяет валидность подписки."""
        follower = attrs.get('follower')
        following = attrs.get('following')

        if follower == following:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя.'
            )

        if follower.subscriptions.filter(following=following).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )

        return attrs
