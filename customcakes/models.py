from django.db import models


class CustomCakeRequest(models.Model):
    STATUS_CHOICES = (
        ('New Request', 'New Request'),
        ('Contacted', 'Contacted'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)

    occasion = models.CharField(max_length=50)
    cake_weight = models.CharField(max_length=50)
    flavour = models.CharField(max_length=100)

    message_on_cake = models.CharField(max_length=255, blank=True)
    special_note = models.TextField(blank=True)
    address = models.TextField()

    reference_image = models.ImageField(
        upload_to='custom_cakes/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='New Request'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name