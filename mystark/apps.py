from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class MystarkConfig(AppConfig):
    name = 'mystark'

    def ready(self):

        autodiscover_modules('stark')

