from django.urls import path

from .views import (
    home,
    newsletter_subscribe,
    about,
    branches,
    privacy_policy,
    return_refund_policy,
)


urlpatterns = [
    path(
        "",
        home,
        name="home",
    ),

    path(
        "about/",
        about,
        name="about",
    ),

    path(
        "branches/",
        branches,
        name="branches",
    ),

    path(
        "newsletter/subscribe/",
        newsletter_subscribe,
        name="newsletter_subscribe",
    ),

    path(
        "privacy-policy/",
        privacy_policy,
        name="privacy_policy",
    ),

    path(
        "return-refund-policy/",
        return_refund_policy,
        name="return_refund_policy",
    ),
]