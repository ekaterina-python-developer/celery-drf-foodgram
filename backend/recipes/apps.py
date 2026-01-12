from django.apps import AppConfig

class RecipesConfig(AppConfig):
    """
    Configuration class for the 'recipes' app.

    Attributes:
        name (str): The name of the app.
        verbose_name (str): The human-readable name for the app.
    """
    name = 'recipes'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Рецепты'
    def ready(self):
        from . import signals  
