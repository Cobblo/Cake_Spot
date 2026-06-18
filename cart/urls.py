from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name='cart'),

    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    path('increase/<int:item_id>/', views.increase_cart, name='increase_cart'),
    path('decrease/<int:item_id>/', views.decrease_cart, name='decrease_cart'),
    path('remove/<int:item_id>/', views.remove_cart, name='remove_cart'),
]