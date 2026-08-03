from django.contrib import messages
from django.shortcuts import render, redirect

from products.models import Product, Category
from .models import NewsletterSubscriber


def home(request):
    best_sellers = Product.objects.filter(
        is_best_seller=True,
        is_available=True
    )[:4]

    home_category_names = [
        "Birthday Cakes",
        "Wedding Cakes",
        "Anniversary Cakes",
    ]

    home_categories = Category.objects.filter(
        name__in=home_category_names
    )

    return render(request, "home.html", {
        "best_sellers": best_sellers,
        "home_categories": home_categories,
    })


def newsletter_subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if email:
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email
            )

            if created:
                messages.success(
                    request,
                    "Thanks! We will send newsletter updates to your email."
                )
            else:
                messages.info(
                    request,
                    "You are already subscribed to our newsletter."
                )
        else:
            messages.error(
                request,
                "Please enter a valid email address."
            )

    return redirect(request.META.get("HTTP_REFERER", "/"))


def about(request):
    return render(request, "products/about.html")


def branches(request):
    return render(request, "products/branches.html")


def privacy_policy(request):
    return render(request, "pages/privacy_policy.html")


def return_refund_policy(request):
    return render(request, "pages/return_refund_policy.html")