from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """Разрешение для автора, персонала или только для чтения."""

    def has_permission(self, request, view):
        """Разрешает безопасные методы всем или аутентифицированным."""
        return (
            request.method in SAFE_METHODS
            or request.user and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """Проверяет права конкретного пользователя на объект."""
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        owner = getattr(
            obj,
            'author',
            None) or getattr(
            obj,
            'user',
            None) or getattr(
            obj,
            'owner',
            None)

        return owner == user or user.is_superuser
