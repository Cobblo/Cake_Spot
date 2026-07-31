import logging

import requests
from django.conf import settings
from django.utils import timezone

from orders.models import Order


logger = logging.getLogger(__name__)


class WhatsAppNotificationError(Exception):
    """Raised when a WhatsApp notification cannot be sent."""


# =========================================================
# BRANCH NUMBER
# =========================================================

def get_branch_whatsapp_number(order):
    """
    Return the WhatsApp number configured for the branch
    selected by the customer.
    """

    branch_numbers = getattr(
        settings,
        "BRANCH_WHATSAPP_NUMBERS",
        {},
    )

    location = str(
        order.location or ""
    ).strip()

    phone_number = branch_numbers.get(
        location,
        "",
    )

    return str(phone_number).strip()


# =========================================================
# ORDER ITEM TEXT
# =========================================================

def clean_template_text(value):
    """
    Convert a value into WhatsApp template-safe text.

    Meta template parameters cannot contain line breaks,
    tab characters, or excessive consecutive spaces.
    """

    text = str(value or "")
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = " ".join(text.split())

    return text.strip()


def build_order_items_text(order):
    """
    Build a single-line value for the approved WhatsApp
    template variable {{items}}.
    """

    item_parts = []

    order_items = (
        order.items
        .select_related("product")
        .prefetch_related("addons")
        .all()
    )

    for index, item in enumerate(
        order_items,
        start=1,
    ):
        product_name = (
            item.product.name
            if item.product
            else "Deleted product"
        )

        quantity = item.quantity or 0
        weight = item.weight or "Not selected"
        cake_message = item.message or "No message"

        addon_names = list(
            item.addons.values_list(
                "name",
                flat=True,
            )
        )

        addon_text = (
            ", ".join(addon_names)
            if addon_names
            else "No add-ons"
        )

        item_text = (
            f"{index}. {product_name} | "
            f"Weight: {weight} | "
            f"Quantity: {quantity} | "
            f"Cake Message: {cake_message} | "
            f"Add-ons: {addon_text}"
        )

        item_parts.append(
            clean_template_text(item_text)
        )

    if not item_parts:
        return "No order items found"

    items_text = " ; ".join(item_parts)

    if len(items_text) > 900:
        items_text = (
            items_text[:897]
            + "..."
        )

    return clean_template_text(items_text)


# =========================================================
# TEMPLATE PARAMETERS
# =========================================================

def build_template_parameters(order):
    """
    Build the named variables used by the approved template:

    {{order_number}}
    {{customer_name}}
    {{phone}}
    {{branch}}
    {{items}}
    {{grand_total}}
    {{payment_method}}
    {{payment_status}}
    """

    customer_name = (
        f"{order.first_name or ''} "
        f"{order.last_name or ''}"
    ).strip()

    if not customer_name:
        customer_name = "Customer"

    return [
        {
            "type": "text",
            "parameter_name": "order_number",
            "text": clean_template_text(
                order.order_number
                or order.pk
            ),
        },
        {
            "type": "text",
            "parameter_name": "customer_name",
            "text": clean_template_text(
                customer_name
            ),
        },
        {
            "type": "text",
            "parameter_name": "phone",
            "text": clean_template_text(
                order.phone
                or "Not provided"
            ),
        },
        {
            "type": "text",
            "parameter_name": "branch",
            "text": clean_template_text(
                order.location
                or "Not selected"
            ),
        },
        {
            "type": "text",
            "parameter_name": "items",
            "text": build_order_items_text(
                order
            ),
        },
        {
            "type": "text",
            "parameter_name": "grand_total",
            "text": clean_template_text(
                format(
                    order.grand_total or 0,
                    ".2f",
                )
            ),
        },
        {
            "type": "text",
            "parameter_name": "payment_method",
            "text": clean_template_text(
                order.payment_method
                or "Not provided"
            ),
        },
        {
            "type": "text",
            "parameter_name": "payment_status",
            "text": clean_template_text(
                order.payment_status
                or "Pending"
            ),
        },
    ]


# =========================================================
# SEND WHATSAPP TEMPLATE
# =========================================================

def send_branch_order_whatsapp(order):
    """
    Send the approved cake_spot_new_order WhatsApp template
    to the branch selected in the order.

    Returns:
        dict: WhatsApp API result.
    """

    notifications_enabled = getattr(
        settings,
        "WHATSAPP_NOTIFICATIONS_ENABLED",
        False,
    )

    if not notifications_enabled:
        logger.info(
            "WhatsApp notification disabled for order %s.",
            order.order_number,
        )

        return {
            "success": False,
            "skipped": True,
            "reason": (
                "WhatsApp notifications are disabled."
            ),
        }

    if order.whatsapp_notification_sent:
        logger.info(
            "WhatsApp notification already sent for order %s.",
            order.order_number,
        )

        return {
            "success": True,
            "skipped": True,
            "reason": (
                "WhatsApp notification already sent."
            ),
            "message_id": (
                order.whatsapp_message_id
            ),
        }

    access_token = str(
        getattr(
            settings,
            "WHATSAPP_ACCESS_TOKEN",
            "",
        )
    ).strip()

    phone_number_id = str(
        getattr(
            settings,
            "WHATSAPP_PHONE_NUMBER_ID",
            "",
        )
    ).strip()

    api_version = str(
        getattr(
            settings,
            "WHATSAPP_API_VERSION",
            "v25.0",
        )
    ).strip()

    template_name = str(
        getattr(
            settings,
            "WHATSAPP_ORDER_TEMPLATE_NAME",
            "cake_spot_new_order",
        )
    ).strip()

    template_language = str(
        getattr(
            settings,
            "WHATSAPP_ORDER_TEMPLATE_LANGUAGE",
            "en",
        )
    ).strip()

    recipient_number = (
        get_branch_whatsapp_number(
            order
        )
    )

    if not access_token:
        error_message = (
            "WhatsApp access token is missing."
        )

        save_whatsapp_error(
            order=order,
            recipient_number=(
                recipient_number
            ),
            error_message=error_message,
        )

        return {
            "success": False,
            "error": error_message,
        }

    if not phone_number_id:
        error_message = (
            "WhatsApp phone number ID is missing."
        )

        save_whatsapp_error(
            order=order,
            recipient_number=(
                recipient_number
            ),
            error_message=error_message,
        )

        return {
            "success": False,
            "error": error_message,
        }

    if not recipient_number:
        error_message = (
            "No WhatsApp number configured for "
            f"branch: {order.location}"
        )

        save_whatsapp_error(
            order=order,
            recipient_number="",
            error_message=error_message,
        )

        return {
            "success": False,
            "error": error_message,
        }

    if not template_name:
        error_message = (
            "WhatsApp template name is missing."
        )

        save_whatsapp_error(
            order=order,
            recipient_number=(
                recipient_number
            ),
            error_message=error_message,
        )

        return {
            "success": False,
            "error": error_message,
        }

    api_url = (
        f"https://graph.facebook.com/"
        f"{api_version}/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": template_language,
            },
            "components": [
                {
                    "type": "body",
                    "parameters": (
                        build_template_parameters(
                            order
                        )
                    ),
                }
            ],
        },
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        try:
            response_data = response.json()

        except ValueError:
            response_data = {
                "raw_response": response.text,
            }

    except requests.Timeout:
        error_message = (
            "WhatsApp API request timed out."
        )

        save_whatsapp_error(
            order=order,
            recipient_number=(
                recipient_number
            ),
            error_message=error_message,
        )

        logger.exception(
            "WhatsApp API timeout for order %s.",
            order.order_number,
        )

        return {
            "success": False,
            "error": error_message,
        }

    except requests.RequestException as error:
        error_message = (
            "WhatsApp API connection error: "
            f"{error}"
        )

        save_whatsapp_error(
            order=order,
            recipient_number=(
                recipient_number
            ),
            error_message=error_message,
        )

        logger.exception(
            "WhatsApp connection error for order %s.",
            order.order_number,
        )

        return {
            "success": False,
            "error": error_message,
        }

    if not response.ok:
        api_error = response_data.get(
            "error",
            {},
        )

        error_message = api_error.get(
            "message",
            (
                "WhatsApp template message "
                "could not be sent."
            ),
        )

        error_code = api_error.get("code")

        error_subcode = api_error.get(
            "error_subcode"
        )

        error_details = (
            api_error
            .get("error_data", {})
            .get("details", "")
        )

        error_parts = [
            str(error_message),
        ]

        if error_code:
            error_parts.append(
                f"Code: {error_code}"
            )

        if error_subcode:
            error_parts.append(
                f"Subcode: {error_subcode}"
            )

        if error_details:
            error_parts.append(
                f"Details: {error_details}"
            )

        complete_error = " | ".join(
            error_parts
        )

        save_whatsapp_error(
            order=order,
            recipient_number=(
                recipient_number
            ),
            error_message=complete_error,
        )

        logger.error(
            "WhatsApp API error for order %s: %s",
            order.order_number,
            response_data,
        )

        return {
            "success": False,
            "error": complete_error,
            "response": response_data,
        }

    messages = response_data.get(
        "messages",
        [],
    )

    message_id = ""

    if messages:
        message_id = messages[0].get(
            "id",
            "",
        )

    sent_at = timezone.now()

    Order.objects.filter(
        pk=order.pk
    ).update(
        whatsapp_notification_sent=True,
        whatsapp_notification_sent_at=(
            sent_at
        ),
        whatsapp_recipient_number=(
            recipient_number
        ),
        whatsapp_message_id=message_id,
        whatsapp_error="",
    )

    order.whatsapp_notification_sent = True

    order.whatsapp_notification_sent_at = (
        sent_at
    )

    order.whatsapp_recipient_number = (
        recipient_number
    )

    order.whatsapp_message_id = message_id

    order.whatsapp_error = ""

    logger.info(
        "WhatsApp template %s sent for order %s to %s.",
        template_name,
        order.order_number,
        recipient_number,
    )

    return {
        "success": True,
        "message_id": message_id,
        "recipient": recipient_number,
        "template": template_name,
        "response": response_data,
    }


# =========================================================
# SAVE ERROR
# =========================================================

def save_whatsapp_error(
    order,
    recipient_number,
    error_message,
):
    """
    Save WhatsApp API errors without interrupting
    customer order placement.
    """

    error_message = str(
        error_message
    )[:2000]

    Order.objects.filter(
        pk=order.pk
    ).update(
        whatsapp_notification_sent=False,
        whatsapp_notification_sent_at=None,
        whatsapp_recipient_number=(
            recipient_number
        ),
        whatsapp_message_id="",
        whatsapp_error=error_message,
    )

    order.whatsapp_notification_sent = False
    order.whatsapp_notification_sent_at = None

    order.whatsapp_recipient_number = (
        recipient_number
    )

    order.whatsapp_message_id = ""

    order.whatsapp_error = error_message