from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import (AvatarSerializer, SubscriptionSerializer,
                             UnsubscribeSerializer, UserSubscriptionSerializer)
from backend.mixins import CreateDeleteMixin

User = get_user_model()


class UserSubscribeView(CreateDeleteMixin, UserViewSet):
    """Кастомный ViewSet для подписок пользователей."""

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от действия."""
        if self.action in ('avatar', 'delete_avatar'):
            return AvatarSerializer
        if self.action == 'subscribe':
            return SubscriptionSerializer
        if self.action == 'unsubscribe':
            return UnsubscribeSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        queryset = request.user.subscriptions.all()
        page = self.paginate_queryset(queryset)
        serializer = UserSubscriptionSerializer(
            [subscription.following for subscription in page],
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        """Подписаться на пользователя."""
        follower = request.user
        following = get_object_or_404(User, id=id)

        serializer = self.get_serializer(
            data={'follower': follower.id, 'following': following.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_data = UserSubscriptionSerializer(
            following, context={'request': request}
        ).data
        return Response(user_data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        """Отписаться от пользователя."""
        serializer = self.get_serializer(data={'following_id': id})
        serializer.is_valid(raise_exception=True)

        request.user.subscriptions.filter(following_id=id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        """Обновление аватара пользователя."""
        serializer = self.get_serializer(
            instance=request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        serializer = self.get_serializer(
            instance=request.user,
            data={'avatar': None}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
