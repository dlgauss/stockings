from django.urls import path

from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.home, name='home'),
    path('thank-you/', views.thanks, name='thanks'),
    path('<slug:kind>/', views.legal, name='legal'),
]
