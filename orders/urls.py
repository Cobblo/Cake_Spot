from django.urls import path

from . import views

urlpatterns = [
    # Checkout
    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),

    # Initial payment
    path(
        "payment/",
        views.payment_page,
        name="payment_page",
    ),

    path(
        "payment-success/",
        views.payment_success,
        name="payment_success",
    ),

    # Balance payment
    path(
        "pay-balance/<str:order_number>/",
        views.pay_balance,
        name="pay_balance",
    ),

    path(
        "balance-payment-success/",
        views.balance_payment_success,
        name="balance_payment_success",
    ),

    # Order success
    path(
        "order-success/<str:order_number>/",
        views.order_success,
        name="order_success",
    ),
]