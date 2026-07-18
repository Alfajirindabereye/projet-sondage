from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('compte/', include('accounts.urls')),
    path('', include('surveys.urls')),
]

if settings.DEBUG:
    admin.site.site_header = "Administration — Système de sondage"
