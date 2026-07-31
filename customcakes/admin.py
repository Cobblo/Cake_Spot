from django.contrib import admin
from .models import CustomCakeRequest


@admin.register(CustomCakeRequest)
class CustomCakeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phone',
        'occasion',
        'cake_weight',
        'created_at',
    )

    search_fields = (
        'name',
        'phone',
        'email',
    )

    list_filter = (
        'occasion',
        'cake_weight',
        'created_at',
    )