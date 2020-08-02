from django.apps import AppConfig

class personalConfig(AppConfig):
    name = 'personal'
    def ready(self):
        from personal.updater import start
        start()
