from django.apps import AppConfig


class MemoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.memories'
    verbose_name = 'Memory Time Machine'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import apps.memories.signals
        except ImportError:
            pass