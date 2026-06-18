from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from .models import CartItem
from products.models import Product


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":

        CartItem.objects.create(
            product=product,
            egg_type=request.POST.get('egg_type'),
            weight=request.POST.get('weight'),
            message=request.POST.get('message'),
            price=request.POST.get('price')
        )

        messages.success(request, "Product added to cart successfully.")

        return redirect('product_detail', slug=product.slug)

    return redirect('product_detail', slug=product.slug)


def cart(request):
    cart_items = CartItem.objects.all()

    total = 0

    for item in cart_items:
        item.row_total = float(item.price) * item.quantity
        total += item.row_total

    if total == 0:
        shipping = 0
    elif total >= 1199:
        shipping = 0
    else:
        shipping = 60

    grand_total = total + shipping

    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'shipping': shipping,
        'grand_total': grand_total,
    })


def increase_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.quantity += 1
    item.save()

    return redirect('cart')


def decrease_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()

    return redirect('cart')


def remove_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()

    return redirect('cart') 