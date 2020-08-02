from django.contrib import admin

from .models import  APIKey, KrogerServiceData

admin.site.register(APIKey)
admin.site.register(KrogerServiceData)