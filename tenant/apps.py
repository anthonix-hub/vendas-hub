from django.apps import AppConfig


class TenantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenant'


class TenantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenant'

    def ready(self):
        import tenant.signals  # Ensure signals are loaded

class TenantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenant'
    def ready(self):
        # Import and start the scheduler
        from tenant.scheduler import start
        start()
