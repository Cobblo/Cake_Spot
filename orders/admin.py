from django.contrib import admin

from .models import Order, OrderItem, OrderPayment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    show_change_link = True

    readonly_fields = (
        "product",
        "weight",
        "message",
        "quantity",
        "price",
        "sub_total_display",
    )

    fields = (
        "product",
        "weight",
        "message",
        "quantity",
        "price",
        "sub_total_display",
    )

    def sub_total_display(self, obj):
        return obj.sub_total

    sub_total_display.short_description = "Subtotal"


class OrderPaymentInline(admin.TabularInline):
    model = OrderPayment
    extra = 0
    show_change_link = True

    readonly_fields = (
        "payment_type",
        "payment_method",
        "amount",
        "status",
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "paid_at",
        "created_at",
    )

    fields = (
        "payment_type",
        "payment_method",
        "amount",
        "status",
        "razorpay_order_id",
        "razorpay_payment_id",
        "paid_at",
        "created_at",
    )

    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "first_name",
        "location",
        "phone",
        "payment_option",
        "payment_status",
        "paid_amount",
        "balance_amount",
        "grand_total",
        "whatsapp_notification_sent",
        "status",
        "created_at",
    )

    list_editable = (
        "status",
    )

    search_fields = (
        "order_number",
        "first_name",
        "last_name",
        "phone",
        "email",
        "location",
        "whatsapp_recipient_number",
        "whatsapp_message_id",
        "razorpay_order_id",
        "razorpay_payment_id",
    )

    list_filter = (
        "status",
        "payment_status",
        "payment_option",
        "payment_method",
        "location",
        "whatsapp_notification_sent",
        "created_at",
    )

    readonly_fields = (
        "order_number",
        "user",
        "total",
        "shipping",
        "grand_total",
        "advance_percentage",
        "paid_amount",
        "balance_amount",
        "payment_status",
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "whatsapp_notification_sent",
        "whatsapp_notification_sent_at",
        "whatsapp_recipient_number",
        "whatsapp_message_id",
        "whatsapp_error",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "order_number",
                    "user",
                    "status",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            "Customer Details",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "address",
                    "city",
                    "pincode",
                    "location",
                    "order_note",
                )
            },
        ),
        (
            "Amount Details",
            {
                "fields": (
                    "total",
                    "shipping",
                    "grand_total",
                    "advance_percentage",
                    "paid_amount",
                    "balance_amount",
                )
            },
        ),
        (
            "Payment Details",
            {
                "fields": (
                    "payment_method",
                    "payment_option",
                    "payment_status",
                    "razorpay_order_id",
                    "razorpay_payment_id",
                    "razorpay_signature",
                )
            },
        ),
        (
            "WhatsApp Notification",
            {
                "fields": (
                    "whatsapp_notification_sent",
                    "whatsapp_notification_sent_at",
                    "whatsapp_recipient_number",
                    "whatsapp_message_id",
                    "whatsapp_error",
                )
            },
        ),
    )

    inlines = [
        OrderItemInline,
        OrderPaymentInline,
    ]

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "weight",
        "quantity",
        "price",
        "sub_total_display",
        "created_at",
    )

    search_fields = (
        "order__order_number",
        "product__name",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "order",
        "product",
        "weight",
        "message",
        "quantity",
        "price",
        "created_at",
    )

    filter_horizontal = (
        "addons",
    )

    def sub_total_display(self, obj):
        return obj.sub_total

    sub_total_display.short_description = "Subtotal"


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "payment_type",
        "payment_method",
        "amount",
        "status",
        "paid_at",
        "created_at",
    )

    search_fields = (
        "order__order_number",
        "razorpay_order_id",
        "razorpay_payment_id",
    )

    list_filter = (
        "payment_type",
        "payment_method",
        "status",
        "created_at",
    )

    readonly_fields = (
        "order",
        "payment_type",
        "payment_method",
        "amount",
        "status",
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "paid_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )