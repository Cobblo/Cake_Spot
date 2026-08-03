from django.shortcuts import render, get_object_or_404

from .models import Product, Category


def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug
    )

    weight_prices = product.weight_prices.all().order_by("id")
    default_weight = weight_prices.filter(
        is_default=True
    ).first()

    if not default_weight:
        default_weight = weight_prices.first()

    return render(request, "products/product_detail.html", {
        "product": product,
        "weight_prices": weight_prices,
        "default_weight": default_weight,
    })


def categories(request):
    categories_list = Category.objects.all()

    products = Product.objects.filter(
        is_available=True
    )

    selected_category = request.GET.get("category")
    selected_category_obj = None

    if selected_category:
        selected_category_obj = Category.objects.filter(
            slug=selected_category
        ).first()

        if selected_category_obj:
            products = products.filter(
                category=selected_category_obj
            )
        else:
            selected_category = None

    return render(request, "products/categories.html", {
        "categories": categories_list,
        "products": products,
        "selected_category": selected_category,
        "selected_category_obj": selected_category_obj,
    })


def search(request):
    keyword = request.GET.get("keyword", "")

    products = Product.objects.filter(
        name__icontains=keyword,
        is_available=True
    )

    return render(request, "products/search_results.html", {
        "products": products,
        "keyword": keyword,
    })


def category_products(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug
    )

    products = Product.objects.filter(
        category=category,
        is_available=True
    )

    context = {
        "category": category,
        "products": products,
    }

    return render(
        request,
        "products/category_products.html",
        context
    )