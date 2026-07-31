import re

from decimal import Decimal

from django.db import models

from products.models import Product, ProductAddon


class CartItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )

    weight = models.CharField(
        max_length=50,
        blank=True,
    )

    message = models.CharField(
        max_length=255,
        blank=True,
    )

    addons = models.ManyToManyField(
        ProductAddon,
        blank=True,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    addon_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    @property
    def row_total(self):
        price = self.price or Decimal("0.00")
        quantity = self.quantity or 0

        return price * quantity

    @property
    def selected_weight_in_kg(self):
        """
        Converts weight values like:

        1/2 Kg
        ½ Kg
        1 Kg
        1.5 Kg
        2 Kg
        500 g
        500 gm

        into kilograms.
        """

        if not self.weight:
            return Decimal("0.00")

        weight_text = str(self.weight).strip().lower()

        # Handle 1/2 Kg
        fraction_match = re.search(
            r"(\d+)\s*/\s*(\d+)",
            weight_text,
        )

        if fraction_match:
            numerator = Decimal(
                fraction_match.group(1)
            )

            denominator = Decimal(
                fraction_match.group(2)
            )

            if denominator == 0:
                return Decimal("0.00")

            return numerator / denominator

        # Handle symbols like ½
        if "½" in weight_text:
            return Decimal("0.50")

        if "¼" in weight_text:
            return Decimal("0.25")

        if "¾" in weight_text:
            return Decimal("0.75")

        # Handle decimal numbers
        number_match = re.search(
            r"(\d+(?:\.\d+)?)",
            weight_text,
        )

        if not number_match:
            return Decimal("0.00")

        try:
            weight_value = Decimal(
                number_match.group(1)
            )
        except Exception:
            return Decimal("0.00")

        # Convert grams to Kg
        if (
            "gram" in weight_text
            or "gm" in weight_text
            or re.search(r"\bg\b", weight_text)
        ):
            return weight_value / Decimal("1000")

        return weight_value

    @property
    def purchased_weight_in_kg(self):
        """
        Total purchased cake weight.
        """

        return (
            self.selected_weight_in_kg
            * Decimal(str(self.quantity))
        )

    @property
    def free_cake_weight_in_kg(self):
        """
        Offer:

        Every completed 1 Kg purchased
        gives ½ Kg FREE.

        Examples

        0.5 Kg -> 0

        1 Kg -> 0.5

        1.5 Kg -> 0.5

        2 Kg -> 1

        3 Kg -> 1.5
        """

        completed_kg = int(
            self.purchased_weight_in_kg
        )

        return Decimal(completed_kg) * Decimal("0.50")

    @property
    def has_free_cake_offer(self):
        return self.free_cake_weight_in_kg > Decimal("0.00")

    @property
    def free_cake_weight_display(self):

        free = self.free_cake_weight_in_kg

        if free <= 0:
            return ""

        if free == Decimal("0.50"):
            return "½ Kg"

        if free == Decimal("1.00"):
            return "1 Kg"

        if free == Decimal("1.50"):
            return "1½ Kg"

        if free == Decimal("2.00"):
            return "2 Kg"

        return f"{free.normalize()} Kg"

    def __str__(self):
        return (
            self.product.name
            if self.product
            else "Cart Item"
        )