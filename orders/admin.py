from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'product',
        'egg_type',
        'weight',
        'message',
        'quantity',
        'price',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'first_name',
        'phone',
        'grand_total',
        'status',
        'created_at',
    )

    list_editable = ('status',)

    search_fields = (
        'order_number',
        'first_name',
        'last_name',
        'phone',
        'email',
    )

    list_filter = (
        'status',
        'created_at',
    )

    readonly_fields = (
        'order_number',
        'total',
        'shipping',
        'grand_total',
        'created_at',
    )

    inlines = [OrderItemInline]