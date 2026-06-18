from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from cart.models import CartItem
from .models import Order, OrderItem


def checkout(request):
    cart_items = CartItem.objects.all()

    if not cart_items:
        return redirect('cart')

    total = 0

    for item in cart_items:
        item.row_total = item.price * item.quantity
        total += item.row_total

    shipping = 0 if total >= 1199 else 60
    grand_total = total + shipping

    if request.method == "POST":
        order = Order.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            order_note=request.POST.get('order_note'),

            total=total,
            shipping=shipping,
            grand_total=grand_total,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                egg_type=item.egg_type,
                weight=item.weight,
                message=item.message,
                quantity=item.quantity,
                price=item.price,
            )

        customer_subject = "Cake Spot - Order Placed Successfully"

        customer_message = f"""
Thank you for ordering from Cake Spot!

Order Number: {order.order_number}
Grand Total: ₹{order.grand_total}

We will contact you shortly to confirm your cake order.

Cake Spot
"""

        send_mail(
            customer_subject,
            customer_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=False,
        )

        admin_subject = f"New Order Received - {order.order_number}"

        admin_message = f"""
New order received!

Order Number: {order.order_number}
Customer: {order.first_name} {order.last_name}
Phone: {order.phone}
Email: {order.email}
Grand Total: ₹{order.grand_total}

Please check admin panel for full details.
"""

        send_mail(
            admin_subject,
            admin_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        cart_items.delete()

        return redirect('order_success', order_number=order.order_number)

    context = {
        'cart_items': cart_items,
        'total': total,
        'shipping': shipping,
        'grand_total': grand_total,
    }

    return render(request, 'orders/checkout.html', context)


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    return render(request, 'orders/order_success.html', {
        'order': order
    })