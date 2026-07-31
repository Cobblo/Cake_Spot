from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

from .forms import SignupForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required

def signup(request):

    if request.method == 'POST':

        form = SignupForm(request.POST)

        if form.is_valid():

            full_name = form.cleaned_data['first_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']

            username = email

            user = User.objects.create_user(
                username=username,
                first_name=full_name,
                email=email,
                password=form.cleaned_data['password1']
            )

            UserProfile.objects.create(
                user=user,
                phone=phone
            )

            login(request, user)

            return redirect('home')

    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {
        'form': form
    })


def user_login(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user:
            login(request, user)
            return redirect('home')

    return render(request, 'accounts/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

@login_required(login_url='login')
def my_account(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    orders = []
    try:
        from orders.models import Order
        orders = Order.objects.filter(user=request.user).order_by('-id')
    except:
        orders = []

    return render(request, 'accounts/my_account.html', {
        'profile': profile,
        'orders': orders,
    })