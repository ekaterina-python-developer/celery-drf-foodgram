from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


class CreateDeleteMixin:
    """Миксин для добавления и удаления объектов (избранное, корзина)."""

    def create_item(self, model, serializer_class, data, request):
        """Создает объект, если его еще нет."""
        user_id = data.get('user')
        recipe_id = data.get('recipe')

        if model.objects.filter(user_id=user_id, recipe_id=recipe_id).exists():
            return Response({'detail': 'Уже добавлено.'},
                            status=status.HTTP_200_OK)

        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_item(self, model, **kwargs):
        """Удаляет объект модели."""
        obj = get_object_or_404(model, **kwargs)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
