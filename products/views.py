from django.shortcuts import render, get_object_or_404
from .models import Product
from .models import Category

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    weight_prices = product.weight_prices.all().order_by('id')
    default_weight = weight_prices.filter(is_default=True).first()

    if not default_weight:
        default_weight = weight_prices.first()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'weight_prices': weight_prices,
        'default_weight': default_weight,
    })

def categories(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)

    selected_category = request.GET.get('category')

    if selected_category:
        category = get_object_or_404(Category, slug=selected_category)
        products = products.filter(category=category)

    return render(request, 'products/categories.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
    })