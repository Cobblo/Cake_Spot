from django.contrib import admin
from .models import (
    Product,
    ProductImage,
    ProductWeightPrice,
    ProductAddon,
    Category,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4


class ProductWeightPriceInline(admin.TabularInline):
    model = ProductWeightPrice
    extra = 6


class ProductAddonInline(admin.TabularInline):
    model = ProductAddon
    extra = 4


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku',
        'name',
        'price',
        'is_best_seller',
        'is_available',
    )

    list_editable = (
        'price',
        'is_best_seller',
        'is_available',
    )

    search_fields = (
        'sku',
        'name',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }

    fields = (
        'sku',
        'name',
        'slug',
        'category',
        'price',
        'image',
        'description',
        'is_best_seller',
        'is_available',
    )

    inlines = [
        ProductImageInline,
        ProductWeightPriceInline,
        ProductAddonInline,
    ]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }