import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(username):
    """Проверяет валидность имени пользователя."""
    if username.lower() in settings.FORBIDDEN_USERNAMES:
        raise ValidationError(
            f'Вы не можете использовать {username} в качестве имени '
            'пользователя.'
        )
    invalid_chars = set(re.findall(r'[^\w.@+-]', username))
    if invalid_chars:
        invalid_chars_str = ','.join(invalid_chars)
        raise ValidationError(
            f'Имя пользователя содержит недопустимые символы: '
            f'{invalid_chars_str}'
        )
