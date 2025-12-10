from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Use the full path for consistency with settings.py if necessary, but 'users' is sufficient if INSTALLED_APPS is set correctly.
    name = 'apps.users' 
    label = 'users'
    