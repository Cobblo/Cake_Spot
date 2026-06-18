from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.categories, name='categories'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]