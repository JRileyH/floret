import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from user_agents import parse

from account.forms import (
    PasswordResetForm,
    RequestPasswordResetForm,
)
from common.integrations.postmark import client as postmark

logger = logging.getLogger(__name__)


@login_required
def password_reset(request):
    """Sends a password reset email."""
    if request.method == "POST":
        form = PasswordResetForm(data=request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["password"])
            request.user.save()
            messages.success(request, message="Password successfully reset!")
            update_session_auth_hash(request, request.user)
            return redirect(to="profile")
    else:
        form = PasswordResetForm()

    return render(request, "form.html", context={"form": form})


def password_reset_confirmation(request):
    return render(request, "password_reset_confirmation.html")


def request_password_reset(request):
    """Sends a password reset email."""
    if request.method == "POST":
        form = RequestPasswordResetForm(request.POST)
        if form.is_valid():
            secret = form.cleaned_data["secret"]
            if secret:
                # Parse user agent for OS and browser info
                user_agent_string = request.META.get("HTTP_USER_AGENT", "")
                user_agent = parse(user_agent_string)

                # Get client IP address (handles proxies/load balancers)
                ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
                if ip_address:
                    ip_address = ip_address.split(",")[0].strip()
                else:
                    ip_address = request.META.get("REMOTE_ADDR", "unknown")

                try:
                    postmark.send_email_template(
                        secret.user.email,
                        settings.POSTMARK_PASSWORD_RESET_TEMPLATE_ID,
                        data={
                            "name": secret.user.first_name
                            if secret.user.first_name
                            else "Stranger",
                            "action_url": secret.magic_link,
                            "product_name": "Floret",
                            "operating_system": user_agent.os.family,
                            "browser_name": user_agent.browser.family,
                            "device_name": user_agent.device.family,
                            "ip_address": ip_address,
                        },
                        tag="Application",
                    )
                except Exception:
                    logger.exception("Failed to sent password reset email")
            return redirect("password_reset_confirmation")
    else:
        form = RequestPasswordResetForm()

    return render(request, "form.html", context={"form": form})
