from django.shortcuts import render, redirect

from .models import CustomCakeRequest


def custom_cakes(request):
    if request.method == "POST":
        CustomCakeRequest.objects.create(
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            email=request.POST.get("email"),
            occasion=request.POST.get("occasion"),
            cake_weight=request.POST.get("cake_weight"),
            flavour=request.POST.get("flavour"),
            message_on_cake=request.POST.get("message_on_cake"),
            special_note=request.POST.get("special_note"),
            address=request.POST.get("address"),
            reference_image=request.FILES.get("reference_image"),
            status="New Request",
        )

        return redirect("custom_cakes_success")

    return render(
        request,
        "customcakes/custom_cakes.html",
    )


def custom_cakes_success(request):
    return render(
        request,
        "customcakes/custom_cakes_success.html",
    )