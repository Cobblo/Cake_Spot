from decimal import Decimal

from django.contrib import messages
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from products.models import (
    Product,
    ProductAddon,
    ProductWeightPrice,
)

from .models import CartItem


def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    if request.method != "POST":
        return redirect(
            "product_detail",
            slug=product.slug,
        )

    weight = request.POST.get(
        "weight",
        "",
    ).strip()

    message = request.POST.get(
        "message",
        "",
    ).strip()

    addon_ids = request.POST.getlist("addons")

    # Get the correct cake price from the database
    base_price = product.price

    if weight:
        selected_weight = ProductWeightPrice.objects.filter(
            product=product,
            weight=weight,
        ).first()

        if selected_weight:
            base_price = selected_weight.price
        else:
            messages.error(
                request,
                "The selected cake weight is invalid.",
            )

            return redirect(
                "product_detail",
                slug=product.slug,
            )

    # Get only valid add-ons
    selected_addons = ProductAddon.objects.filter(
        product=product,
        id__in=addon_ids,
        is_active=True,
    )

    addon_total = sum(
        (
            addon.price
            for addon in selected_addons
        ),
        Decimal("0.00"),
    )

    final_price = base_price + addon_total

    cart_item = CartItem.objects.create(
        product=product,
        weight=weight,
        message=message,
        base_price=base_price,
        addon_total=addon_total,
        price=final_price,
    )

    cart_item.addons.set(selected_addons)

    messages.success(
        request,
        "Product added to cart successfully.",
    )

    return redirect(
        "product_detail",
        slug=product.slug,
    )


def cart(request):
    cart_items = (
        CartItem.objects
        .select_related("product")
        .prefetch_related("addons")
        .all()
        .order_by("-created_at")
    )

    total = sum(
        (
            item.row_total
            for item in cart_items
        ),
        Decimal("0.00"),
    )

    total_free_cake_weight = sum(
        (
            item.free_cake_weight_in_kg
            for item in cart_items
        ),
        Decimal("0.00"),
    )

    if total == Decimal("0.00"):
        shipping = Decimal("0.00")

    elif total >= Decimal("1199.00"):
        shipping = Decimal("0.00")

    else:
        shipping = Decimal("60.00")

    grand_total = total + shipping

    return render(
        request,
        "cart/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
            "shipping": shipping,
            "grand_total": grand_total,
            "total_free_cake_weight": total_free_cake_weight,
        },
    )


def increase_cart(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
    )

    item.quantity += 1
    item.save(
        update_fields=["quantity"],
    )

    return redirect("cart")


def decrease_cart(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
    )

    if item.quantity > 1:
        item.quantity -= 1
        item.save(
            update_fields=["quantity"],
        )

    return redirect("cart")


def remove_cart(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
    )

    item.delete()

    return redirect("cart")