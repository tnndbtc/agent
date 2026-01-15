"""App configuration for novels."""
from django.apps import AppConfig


class NovelsConfig(AppConfig):
    """Configuration for the novels app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'novels'
    verbose_name = 'Novel Writing Agent'

    def ready(self):
        """Import signal handlers."""
        import novels.signals  # noqa
