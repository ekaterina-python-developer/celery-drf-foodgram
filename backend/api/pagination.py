from rest_framework.pagination import PageNumberPagination


class PageNumberPagination(PageNumberPagination):
    """Кастомная пагинация с параметром `limit` для размера страницы."""

    page_size_query_param = 'limit'
