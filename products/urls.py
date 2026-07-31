from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.categories, name='categories'),

    path('category/<slug:category_slug>/',
         views.category_products,
         name='category_products'),

    path('search/', views.search, name='search'),

    path('<slug:slug>/', views.product_detail, name='product_detail'),
]