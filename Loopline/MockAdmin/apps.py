from django.apps import AppConfig


class MockadminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MockAdmin'
