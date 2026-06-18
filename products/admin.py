from django.contrib import admin
from .models import Product, ProductImage, ProductWeightPrice, Category

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4

class ProductWeightPriceInline(admin.TabularInline):
    model = ProductWeightPrice
    extra = 6

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_best_seller', 'is_available')
    list_editable = ('price', 'is_best_seller', 'is_available')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductWeightPriceInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
