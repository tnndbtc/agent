"""App configuration for novels."""
from django.apps import AppConfig


class NovelsConfig(AppConfig):
    """Configuration for the novels app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'novels'
    verbose_name = 'Novel Writing Agent'

    def ready(self):
        """Import signal handlers and apply OpenAI logging patch."""
        import novels.signals  # noqa

        # Apply OpenAI logging patch to log all API calls
        from novels.ai_client import patch_openai_for_logging
        patch_openai_for_logging()
