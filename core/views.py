from django.shortcuts import render
from products.models import Product

def home(request):
    best_sellers = Product.objects.filter(
        is_best_seller=True,
        is_available=True
    )[:4]

    return render(request, 'home.html', {
        'best_sellers': best_sellers
    })