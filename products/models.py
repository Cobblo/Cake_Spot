from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    intro_title = models.CharField(max_length=150, blank=True)
    intro_subtitle = models.CharField(max_length=150, blank=True)
    intro_description = models.TextField(blank=True)
    intro_video = models.FileField(upload_to='category_videos/', blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="SKU"
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_best_seller = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return self.product.name


class ProductWeightPrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='weight_prices')
    weight = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - {self.weight} - ₹{self.price}"


class ProductAddon(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="addons"
    )

    name = models.CharField(max_length=100)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} - {self.name}"