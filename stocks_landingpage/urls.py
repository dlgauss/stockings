"""
URL configuration for stocks_landingpage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from landing import views as landing_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/address/', landing_views.address_suggest, name='address_suggest'),
]

# /ro/... and /ru/...; "/" redirects to the visitor's browser language.
urlpatterns += i18n_patterns(
    path('', include('landing.urls')),
)

handler404 = 'landing.views.page_not_found'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
