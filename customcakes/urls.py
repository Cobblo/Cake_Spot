from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_cakes, name='custom_cakes'),
    path('success/', views.custom_cakes_success, name='custom_cakes_success'),
]