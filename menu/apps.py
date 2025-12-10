"""
Menu App Configuration
"""

from django.apps import AppConfig


class MenuConfig(AppConfig):
    # Use BigAutoField as the default primary key type for models without one defined
    default_auto_field = 'django.db.models.BigAutoField'
    # The name of the application package
    name = 'menu' 
    # Optional: Verbose name for the Admin panel
    verbose_name = 'Menu Management'
    
