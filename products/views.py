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
    selected_category_obj = None

    if selected_category:
        selected_category_obj = get_object_or_404(Category, slug=selected_category)
        products = products.filter(category=selected_category_obj)

    return render(request, 'products/categories.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'selected_category_obj': selected_category_obj,
    })

def search(request):
    keyword = request.GET.get('keyword', '')

    products = Product.objects.filter(
        name__icontains=keyword,
        is_available=True
    )

    return render(request, 'products/search_results.html', {
        'products': products,
        'keyword': keyword
    })

def category_products(request, category_slug):

    category = Category.objects.get(slug=category_slug)

    products = Product.objects.filter(
        category=category,
        is_available=True
    )

    context = {
        'category': category,
        'products': products,
    }

    return render(
        request,
        'products/category_products.html',
        context
    )