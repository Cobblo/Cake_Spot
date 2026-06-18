from .models import CartItem

def cart_counter(request):

    count = sum(item.quantity for item in CartItem.objects.all())

    return {
        'cart_count': count
    }