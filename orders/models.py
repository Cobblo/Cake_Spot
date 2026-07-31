from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product, ProductAddon


class Order(models.Model):

    STATUS = (
        ("Pending", "Pending"),
        ("Advance Paid", "Advance Paid"),
        ("Confirmed", "Confirmed"),
        ("Preparing", "Preparing"),
        ("Out for Delivery", "Out for Delivery"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    )

    PAYMENT_METHODS = (
        ("Online Payment", "Online Payment"),
        ("Cash on Delivery", "Cash on Delivery"),
    )

    PAYMENT_OPTIONS = (
        ("FULL", "Full Payment"),
        ("PARTIAL", "50% Advance Payment"),
        ("COD", "Cash on Delivery"),
    )

    PAYMENT_STATUS = (
        ("Pending", "Pending"),
        ("Partially Paid", "Partially Paid"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
        ("COD Pending", "COD Pending"),
    )

    LOCATION_CHOICES = (
        ("Iyyapanthangal-1", "Iyyapanthangal-1"),
        ("Iyyapanthangal-2", "Iyyapanthangal-2"),
        ("Porur", "Porur"),
        ("Kovur", "Kovur"),
        ("Mangadu", "Mangadu"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="cake_spot_orders",
        null=True,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=15,
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100,
    )

    pincode = models.CharField(
        max_length=10,
    )

    location = models.CharField(
        max_length=50,
        choices=LOCATION_CHOICES,
    )

    order_note = models.TextField(
        blank=True,
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    shipping = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS,
        default="Cash on Delivery",
    )

    payment_option = models.CharField(
        max_length=20,
        choices=PAYMENT_OPTIONS,
        default="FULL",
    )

    advance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("50.00"),
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    balance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS,
        default="Pending",
    )

    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    razorpay_payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    order_number = models.CharField(
        max_length=30,
        blank=True,
        unique=True,
        null=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS,
        default="Pending",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ================= WHATSAPP NOTIFICATION =================

    whatsapp_notification_sent = models.BooleanField(
        default=False,
    )

    whatsapp_notification_sent_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    whatsapp_recipient_number = models.CharField(
        max_length=20,
        blank=True,
    )

    whatsapp_message_id = models.CharField(
        max_length=255,
        blank=True,
    )

    whatsapp_error = models.TextField(
        blank=True,
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.order_number:
            current_year = timezone.localdate().year

            self.order_number = (
                f"CS{current_year}"
                f"{str(self.id).zfill(5)}"
            )

            super().save(
                update_fields=[
                    "order_number",
                ]
            )

    @property
    def advance_amount(self):
        grand_total = (
            self.grand_total
            or Decimal("0.00")
        )

        advance_percentage = (
            self.advance_percentage
            or Decimal("0.00")
        )

        return (
            grand_total
            * advance_percentage
            / Decimal("100.00")
        ).quantize(
            Decimal("0.01")
        )

    @property
    def amount_due(self):
        grand_total = (
            self.grand_total
            or Decimal("0.00")
        )

        paid_amount = (
            self.paid_amount
            or Decimal("0.00")
        )

        balance = (
            grand_total
            - paid_amount
        )

        if balance < Decimal("0.00"):
            return Decimal("0.00")

        return balance

    @property
    def is_partially_paid(self):
        balance_amount = (
            self.balance_amount
            or Decimal("0.00")
        )

        return (
            self.payment_status == "Partially Paid"
            and balance_amount > Decimal("0.00")
        )

    @property
    def is_fully_paid(self):
        balance_amount = (
            self.balance_amount
            or Decimal("0.00")
        )

        return (
            self.payment_status == "Paid"
            and balance_amount <= Decimal("0.00")
        )

    def __str__(self):
        return (
            self.order_number
            or f"Order {self.pk}"
        )


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )

    addons = models.ManyToManyField(
        ProductAddon,
        blank=True,
        related_name="order_items",
    )

    weight = models.CharField(
        max_length=50,
        blank=True,
    )

    message = models.CharField(
        max_length=255,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    @property
    def sub_total(self):
        price = (
            self.price
            or Decimal("0.00")
        )

        quantity = (
            self.quantity
            or 0
        )

        return (
            price
            * quantity
        )

    def __str__(self):
        product_name = (
            self.product.name
            if self.product
            else "Deleted product"
        )

        quantity = (
            self.quantity
            or 0
        )

        return (
            f"{product_name} "
            f"({quantity})"
        )


class OrderPayment(models.Model):

    PAYMENT_TYPES = (
        ("FULL", "Full Payment"),
        ("ADVANCE", "Advance Payment"),
        ("BALANCE", "Balance Payment"),
    )

    PAYMENT_METHODS = (
        ("Razorpay", "Razorpay"),
        ("Cash on Delivery", "Cash on Delivery"),
    )

    PAYMENT_STATUS = (
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS,
        default="Razorpay",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="Pending",
    )

    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    razorpay_payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        amount = (
            self.amount
            or Decimal("0.00")
        )

        return (
            f"{self.order.order_number} - "
            f"{self.get_payment_type_display()} - "
            f"₹{amount}"
        )