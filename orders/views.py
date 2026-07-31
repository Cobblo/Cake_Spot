from decimal import Decimal
from io import BytesIO
from urllib.parse import quote

import razorpay
from xhtml2pdf import pisa

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone

from cart.models import CartItem

from .models import Order, OrderItem, OrderPayment
from .services.whatsapp_service import send_branch_order_whatsapp


# =========================================================
# PDF GENERATION
# =========================================================

def generate_invoice_pdf(
    order,
    document_type="final_invoice",
    payment=None,
):
    """
    document_type values:

    advance_receipt
    final_invoice
    order_confirmation
    """

    template = get_template(
        "orders/invoice.html"
    )

    html = template.render({
        "order": order,
        "payment": payment,
        "payments": order.payments.filter(
            status="Paid"
        ).order_by("created_at"),
        "document_type": document_type,
    })

    result = BytesIO()

    pdf = pisa.pisaDocument(
        BytesIO(
            html.encode("UTF-8")
        ),
        result,
    )

    if pdf.err:
        return None

    return result.getvalue()


# =========================================================
# EMAIL FUNCTIONS
# =========================================================

def send_order_emails(
    order,
    document_type="final_invoice",
    payment=None,
):
    """
    document_type values:

    advance_receipt
    final_invoice
    order_confirmation
    """

    customer_email_address = (
        order.email.strip()
        if order.email
        else ""
    )

    admin_email_address = getattr(
        settings,
        "ADMIN_EMAIL",
        settings.DEFAULT_FROM_EMAIL,
    )

    attachment_pdf = None
    attachment_name = None

    if document_type == "advance_receipt":
        attachment_pdf = generate_invoice_pdf(
            order=order,
            document_type="advance_receipt",
            payment=payment,
        )

        attachment_name = (
            f"Advance-Receipt-"
            f"{order.order_number}.pdf"
        )

        customer_subject = (
            f"Cake Spot - Advance Payment Receipt "
            f"{order.order_number}"
        )

        customer_message = f"""
Dear {order.first_name},

Thank you for your advance payment.

Order Number: {order.order_number}
Order Total: ₹{order.grand_total}
Advance Paid: ₹{order.paid_amount}
Balance Amount: ₹{order.balance_amount}
Payment Status: {order.payment_status}

You can pay the remaining balance later from your account.

Your advance payment receipt is attached to this email.

Cake Spot
"""

        admin_subject = (
            f"Advance Payment Received - "
            f"{order.order_number}"
        )

        admin_message = f"""
Advance payment received.

Order Number: {order.order_number}
Customer: {order.first_name} {order.last_name}
Phone: {order.phone}
Email: {order.email}

Order Total: ₹{order.grand_total}
Advance Paid: ₹{order.paid_amount}
Balance Amount: ₹{order.balance_amount}
Payment Status: {order.payment_status}

Please check the admin panel for full details.
"""

    elif document_type == "final_invoice":
        attachment_pdf = generate_invoice_pdf(
            order=order,
            document_type="final_invoice",
            payment=payment,
        )

        attachment_name = (
            f"Invoice-"
            f"{order.order_number}.pdf"
        )

        customer_subject = (
            f"Cake Spot - Final Invoice "
            f"{order.order_number}"
        )

        customer_message = f"""
Dear {order.first_name},

Thank you for completing your payment.

Order Number: {order.order_number}
Grand Total: ₹{order.grand_total}
Total Paid: ₹{order.paid_amount}
Balance Amount: ₹{order.balance_amount}
Payment Status: {order.payment_status}

Your final invoice is attached to this email.

We will contact you shortly regarding your cake order.

Cake Spot
"""

        admin_subject = (
            f"Full Payment Received - "
            f"{order.order_number}"
        )

        admin_message = f"""
Full payment received.

Order Number: {order.order_number}
Customer: {order.first_name} {order.last_name}
Phone: {order.phone}
Email: {order.email}

Grand Total: ₹{order.grand_total}
Total Paid: ₹{order.paid_amount}
Balance Amount: ₹{order.balance_amount}
Payment Status: {order.payment_status}

Please check the admin panel for full details.
"""

    else:
        customer_subject = (
            f"Cake Spot - Order Confirmation "
            f"{order.order_number}"
        )

        customer_message = f"""
Dear {order.first_name},

Thank you for ordering from Cake Spot.

Order Number: {order.order_number}
Grand Total: ₹{order.grand_total}
Payment Method: {order.payment_method}
Payment Status: {order.payment_status}

We will contact you shortly to confirm your cake order.

Cake Spot
"""

        admin_subject = (
            f"New Order Received - "
            f"{order.order_number}"
        )

        admin_message = f"""
New order received.

Order Number: {order.order_number}
Customer: {order.first_name} {order.last_name}
Phone: {order.phone}
Email: {order.email}
Grand Total: ₹{order.grand_total}
Payment Method: {order.payment_method}
Payment Status: {order.payment_status}

Address:
{order.address}
{order.city} - {order.pincode}

Please check the admin panel for full details.
"""

    if customer_email_address:
        customer_email = EmailMessage(
            subject=customer_subject,
            body=customer_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[
                customer_email_address,
            ],
        )

        if attachment_pdf and attachment_name:
            customer_email.attach(
                attachment_name,
                attachment_pdf,
                "application/pdf",
            )

        customer_email.send(
            fail_silently=False,
        )

    if admin_email_address:
        admin_email = EmailMessage(
            subject=admin_subject,
            body=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[
                admin_email_address,
            ],
        )

        if attachment_pdf and attachment_name:
            admin_email.attach(
                attachment_name,
                attachment_pdf,
                "application/pdf",
            )

        admin_email.send(
            fail_silently=False,
        )


# =========================================================
# CART FUNCTIONS
# =========================================================

def get_cart_items():
    return (
        CartItem.objects
        .select_related("product")
        .prefetch_related("addons")
        .all()
        .order_by("-created_at")
    )


def calculate_cart(cart_items):
    total = sum(
        (
            item.row_total
            for item in cart_items
        ),
        Decimal("0.00"),
    )

    if total == Decimal("0.00"):
        shipping = Decimal("0.00")

    elif total >= Decimal("1199.00"):
        shipping = Decimal("0.00")

    else:
        shipping = Decimal("60.00")

    grand_total = total + shipping

    return (
        total,
        shipping,
        grand_total,
    )


# =========================================================
# RAZORPAY FUNCTIONS
# =========================================================

def get_razorpay_client():
    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )


def create_razorpay_order(amount):
    client = get_razorpay_client()

    amount_in_paise = int(
        amount * Decimal("100")
    )

    razorpay_order = client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1,
    })

    return (
        razorpay_order,
        amount_in_paise,
    )


def verify_razorpay_payment(
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature,
):
    client = get_razorpay_client()

    client.utility.verify_payment_signature({
        "razorpay_order_id": (
            razorpay_order_id
        ),
        "razorpay_payment_id": (
            razorpay_payment_id
        ),
        "razorpay_signature": (
            razorpay_signature
        ),
    })


def get_customer_order(
    request,
    order_number,
):
    if request.user.is_superuser:
        return get_object_or_404(
            Order,
            order_number=order_number,
        )

    return get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )


# =========================================================
# CHECKOUT PAGE
# =========================================================

def checkout(request):
    cart_items = get_cart_items()

    if not cart_items.exists():
        return redirect("cart")

    (
        total,
        shipping,
        grand_total,
    ) = calculate_cart(
        cart_items
    )

    advance_amount = (
        grand_total
        * Decimal("50.00")
        / Decimal("100.00")
    ).quantize(
        Decimal("0.01")
    )

    balance_amount = (
        grand_total
        - advance_amount
    ).quantize(
        Decimal("0.01")
    )

    context = {
        "cart_items": cart_items,
        "total": total,
        "shipping": shipping,
        "grand_total": grand_total,
        "advance_amount": advance_amount,
        "balance_amount": balance_amount,
    }

    return render(
        request,
        "orders/checkout.html",
        context,
    )


# =========================================================
# CREATE ORDER AND OPEN PAYMENT
# =========================================================

@login_required
def payment_page(request):
    cart_items = get_cart_items()

    if not cart_items.exists():
        return redirect("cart")

    (
        total,
        shipping,
        grand_total,
    ) = calculate_cart(
        cart_items
    )

    advance_amount = (
        grand_total
        * Decimal("50.00")
        / Decimal("100.00")
    ).quantize(
        Decimal("0.01")
    )

    if request.method == "POST":
        full_name = request.POST.get(
            "full_name",
            "",
        ).strip()

        name_parts = full_name.split(
            " ",
            1,
        )

        first_name = (
            name_parts[0]
            if name_parts
            else ""
        )

        last_name = (
            name_parts[1]
            if len(name_parts) > 1
            else ""
        )

        payment_method = request.POST.get(
            "payment_method",
            "Online Payment",
        )

        payment_option = request.POST.get(
            "payment_option",
            "FULL",
        ).upper()

        if payment_method == "Cash on Delivery":
            payment_option = "COD"

        if payment_option not in (
            "FULL",
            "PARTIAL",
            "COD",
        ):
            payment_option = "FULL"

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=request.POST.get(
                    "email",
                    request.user.email,
                ).strip(),
                phone=request.POST.get(
                    "phone",
                    "",
                ).strip(),
                address=request.POST.get(
                    "address",
                    "",
                ).strip(),
                city=request.POST.get(
                    "city",
                    "",
                ).strip(),
                pincode=request.POST.get(
                    "pincode",
                    "",
                ).strip(),
                location=request.POST.get(
                    "location",
                    "",
                ).strip(),
                order_note=request.POST.get(
                    "order_note",
                    "",
                ).strip(),
                total=total,
                shipping=shipping,
                grand_total=grand_total,
                payment_method=payment_method,
                payment_option=payment_option,
                advance_percentage=Decimal(
                    "50.00"
                ),
                paid_amount=Decimal(
                    "0.00"
                ),
                balance_amount=grand_total,
                payment_status="Pending",
                status="Pending",
            )

            for item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    weight=item.weight,
                    message=item.message,
                    quantity=item.quantity,
                    price=item.price,
                )

                order_item.addons.set(
                    item.addons.all()
                )

        if payment_option == "COD":
            order.payment_method = (
                "Cash on Delivery"
            )

            order.payment_status = (
                "COD Pending"
            )

            order.balance_amount = (
                order.grand_total
            )

            order.status = "Pending"

            order.save(
                update_fields=[
                    "payment_method",
                    "payment_status",
                    "balance_amount",
                    "status",
                ]
            )

            send_order_emails(
                order=order,
                document_type=(
                    "order_confirmation"
                ),
            )

            send_branch_order_whatsapp(order)

            cart_items.delete()

            return redirect(
                "order_success",
                order_number=(
                    order.order_number
                ),
            )

        if payment_option == "PARTIAL":
            amount_to_pay = advance_amount
            payment_type = "ADVANCE"

        else:
            amount_to_pay = grand_total
            payment_type = "FULL"

        try:
            (
                razorpay_order,
                amount_in_paise,
            ) = create_razorpay_order(
                amount_to_pay
            )

        except Exception as error:
            messages.error(
                request,
                (
                    "Unable to start the payment. "
                    "Please try again."
                ),
            )

            order.payment_status = "Failed"

            order.save(
                update_fields=[
                    "payment_status",
                ]
            )

            return redirect("checkout")

        order.razorpay_order_id = (
            razorpay_order["id"]
        )

        order.save(
            update_fields=[
                "razorpay_order_id",
            ]
        )

        payment = OrderPayment.objects.create(
            order=order,
            payment_type=payment_type,
            payment_method="Razorpay",
            amount=amount_to_pay,
            status="Pending",
            razorpay_order_id=(
                razorpay_order["id"]
            ),
        )

        return render(
            request,
            "orders/razorpay_payment.html",
            {
                "order": order,
                "payment": payment,
                "payment_type": payment_type,
                "razorpay_key": (
                    settings.RAZORPAY_KEY_ID
                ),
                "razorpay_order_id": (
                    razorpay_order["id"]
                ),
                "amount": amount_in_paise,
                "display_amount": (
                    amount_to_pay
                ),
                "payment_success_url": reverse(
                    "payment_success"
                ),
            },
        )

    return render(
        request,
        "orders/payment.html",
        {
            "cart_total": total,
            "shipping": shipping,
            "grand_total": grand_total,
            "advance_amount": (
                advance_amount
            ),
            "balance_amount": (
                grand_total
                - advance_amount
            ),
            "user_email": (
                request.user.email
                if request.user.is_authenticated
                else ""
            ),
        },
    )


# =========================================================
# INITIAL PAYMENT SUCCESS
# =========================================================

@login_required
def payment_success(request):
    if request.method != "POST":
        return redirect("cart")

    order_id = request.POST.get(
        "order_id"
    )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_signature = request.POST.get(
        "razorpay_signature"
    )

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    payment = get_object_or_404(
        OrderPayment,
        order=order,
        razorpay_order_id=(
            razorpay_order_id
        ),
        status="Pending",
    )

    try:
        verify_razorpay_payment(
            razorpay_order_id=(
                payment.razorpay_order_id
            ),
            razorpay_payment_id=(
                razorpay_payment_id
            ),
            razorpay_signature=(
                razorpay_signature
            ),
        )

    except razorpay.errors.SignatureVerificationError:
        payment.status = "Failed"

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        order.payment_status = "Failed"

        order.save(
            update_fields=[
                "payment_status",
            ]
        )

        messages.error(
            request,
            (
                "Payment verification failed. "
                "Please contact Cake Spot."
            ),
        )

        return redirect("checkout")

    with transaction.atomic():
        locked_payment = (
            OrderPayment.objects
            .select_for_update()
            .get(pk=payment.pk)
        )

        locked_order = (
            Order.objects
            .select_for_update()
            .get(pk=order.pk)
        )

        if locked_payment.status == "Paid":
            return redirect(
                "order_success",
                order_number=(
                    locked_order.order_number
                ),
            )

        locked_payment.status = "Paid"
        locked_payment.razorpay_payment_id = (
            razorpay_payment_id
        )
        locked_payment.razorpay_signature = (
            razorpay_signature
        )
        locked_payment.paid_at = timezone.now()

        locked_payment.save(
            update_fields=[
                "status",
                "razorpay_payment_id",
                "razorpay_signature",
                "paid_at",
                "updated_at",
            ]
        )

        locked_order.razorpay_payment_id = (
            razorpay_payment_id
        )
        locked_order.razorpay_signature = (
            razorpay_signature
        )

        locked_order.paid_amount = (
            locked_payment.amount
        )

        locked_order.balance_amount = (
            locked_order.grand_total
            - locked_order.paid_amount
        ).quantize(
            Decimal("0.01")
        )

        if (
            locked_payment.payment_type
            == "ADVANCE"
        ):
            locked_order.payment_status = (
                "Partially Paid"
            )

            locked_order.status = (
                "Advance Paid"
            )

        else:
            locked_order.payment_status = "Paid"
            locked_order.status = "Confirmed"
            locked_order.balance_amount = (
                Decimal("0.00")
            )

        locked_order.save(
            update_fields=[
                "razorpay_payment_id",
                "razorpay_signature",
                "paid_amount",
                "balance_amount",
                "payment_status",
                "status",
            ]
        )

    if payment.payment_type == "ADVANCE":
        send_order_emails(
            order=locked_order,
            document_type=(
                "advance_receipt"
            ),
            payment=locked_payment,
        )

    else:
        send_order_emails(
            order=locked_order,
            document_type=(
                "final_invoice"
            ),
            payment=locked_payment,
        )

    send_branch_order_whatsapp(locked_order)

    CartItem.objects.all().delete()

    return redirect(
        "order_success",
        order_number=(
            locked_order.order_number
        ),
    )


# =========================================================
# PAY REMAINING BALANCE
# =========================================================

@login_required
def pay_balance(
    request,
    order_number,
):
    order = get_customer_order(
        request,
        order_number,
    )

    if order.payment_status == "Paid":
        messages.info(
            request,
            "This order is already fully paid.",
        )

        return redirect(
            "order_success",
            order_number=(
                order.order_number
            ),
        )

    if order.payment_status != "Partially Paid":
        messages.error(
            request,
            (
                "Balance payment is not "
                "available for this order."
            ),
        )

        return redirect(
            "order_success",
            order_number=(
                order.order_number
            ),
        )

    balance_amount = (
        order.grand_total
        - order.paid_amount
    ).quantize(
        Decimal("0.01")
    )

    if balance_amount <= Decimal("0.00"):
        order.balance_amount = Decimal(
            "0.00"
        )

        order.payment_status = "Paid"
        order.status = "Confirmed"

        order.save(
            update_fields=[
                "balance_amount",
                "payment_status",
                "status",
            ]
        )

        return redirect(
            "order_success",
            order_number=(
                order.order_number
            ),
        )

    try:
        (
            razorpay_order,
            amount_in_paise,
        ) = create_razorpay_order(
            balance_amount
        )

    except Exception:
        messages.error(
            request,
            (
                "Unable to start the balance "
                "payment. Please try again."
            ),
        )

        return redirect(
            "order_success",
            order_number=(
                order.order_number
            ),
        )

    payment = OrderPayment.objects.create(
        order=order,
        payment_type="BALANCE",
        payment_method="Razorpay",
        amount=balance_amount,
        status="Pending",
        razorpay_order_id=(
            razorpay_order["id"]
        ),
    )

    return render(
        request,
        "orders/razorpay_payment.html",
        {
            "order": order,
            "payment": payment,
            "payment_type": "BALANCE",
            "razorpay_key": (
                settings.RAZORPAY_KEY_ID
            ),
            "razorpay_order_id": (
                razorpay_order["id"]
            ),
            "amount": amount_in_paise,
            "display_amount": (
                balance_amount
            ),
            "payment_success_url": reverse(
                "balance_payment_success"
            ),
        },
    )


# =========================================================
# BALANCE PAYMENT SUCCESS
# =========================================================

@login_required
def balance_payment_success(request):
    if request.method != "POST":
        return redirect("checkout")

    order_id = request.POST.get(
        "order_id"
    )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_signature = request.POST.get(
        "razorpay_signature"
    )

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    payment = get_object_or_404(
        OrderPayment,
        order=order,
        payment_type="BALANCE",
        razorpay_order_id=(
            razorpay_order_id
        ),
        status="Pending",
    )

    try:
        verify_razorpay_payment(
            razorpay_order_id=(
                payment.razorpay_order_id
            ),
            razorpay_payment_id=(
                razorpay_payment_id
            ),
            razorpay_signature=(
                razorpay_signature
            ),
        )

    except razorpay.errors.SignatureVerificationError:
        payment.status = "Failed"

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.error(
            request,
            (
                "Balance payment verification "
                "failed. Please contact Cake Spot."
            ),
        )

        return redirect(
            "order_success",
            order_number=(
                order.order_number
            ),
        )

    with transaction.atomic():
        locked_payment = (
            OrderPayment.objects
            .select_for_update()
            .get(pk=payment.pk)
        )

        locked_order = (
            Order.objects
            .select_for_update()
            .get(pk=order.pk)
        )

        if locked_payment.status == "Paid":
            return redirect(
                "order_success",
                order_number=(
                    locked_order.order_number
                ),
            )

        locked_payment.status = "Paid"
        locked_payment.razorpay_payment_id = (
            razorpay_payment_id
        )
        locked_payment.razorpay_signature = (
            razorpay_signature
        )
        locked_payment.paid_at = timezone.now()

        locked_payment.save(
            update_fields=[
                "status",
                "razorpay_payment_id",
                "razorpay_signature",
                "paid_at",
                "updated_at",
            ]
        )

        total_paid = sum(
            (
                completed_payment.amount
                for completed_payment
                in locked_order.payments.filter(
                    status="Paid"
                )
            ),
            Decimal("0.00"),
        )

        locked_order.paid_amount = (
            total_paid
        ).quantize(
            Decimal("0.01")
        )

        locked_order.balance_amount = (
            locked_order.grand_total
            - locked_order.paid_amount
        ).quantize(
            Decimal("0.01")
        )

        if (
            locked_order.balance_amount
            <= Decimal("0.00")
        ):
            locked_order.balance_amount = (
                Decimal("0.00")
            )

            locked_order.payment_status = "Paid"
            locked_order.status = "Confirmed"

        else:
            locked_order.payment_status = (
                "Partially Paid"
            )

            locked_order.status = (
                "Advance Paid"
            )

        locked_order.razorpay_order_id = (
            locked_payment.razorpay_order_id
        )

        locked_order.razorpay_payment_id = (
            razorpay_payment_id
        )

        locked_order.razorpay_signature = (
            razorpay_signature
        )

        locked_order.save(
            update_fields=[
                "paid_amount",
                "balance_amount",
                "payment_status",
                "status",
                "razorpay_order_id",
                "razorpay_payment_id",
                "razorpay_signature",
            ]
        )

    if locked_order.payment_status == "Paid":
        send_order_emails(
            order=locked_order,
            document_type=(
                "final_invoice"
            ),
            payment=locked_payment,
        )

    return redirect(
        "order_success",
        order_number=(
            locked_order.order_number
        ),
    )


# =========================================================
# ORDER SUCCESS PAGE
# =========================================================

@login_required
def order_success(
    request,
    order_number,
):
    order = get_customer_order(
        request,
        order_number,
    )

    whatsapp_message = f"""
New Cake Spot Order

Order No: {order.order_number}
Customer: {order.first_name} {order.last_name}
Phone: {order.phone}

Grand Total: ₹{order.grand_total}
Paid Amount: ₹{order.paid_amount}
Balance Amount: ₹{order.balance_amount}

Payment Method: {order.payment_method}
Payment Status: {order.payment_status}

Address:
{order.address}
{order.city} - {order.pincode}
"""

    whatsapp_url = (
        "https://wa.me/918220773182?text="
        + quote(
            whatsapp_message
        )
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
            "payments": (
                order.payments
                .filter(status="Paid")
                .order_by("created_at")
            ),
            "whatsapp_url": whatsapp_url,
        },
    )