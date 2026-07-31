from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class SignupForm(UserCreationForm):

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Full Name'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email Address'
        })
    )

    phone = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': 'Phone Number'
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create Password'
        })
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'email',
            'phone',
            'password1',
            'password2'
        )