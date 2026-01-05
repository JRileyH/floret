import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.utils import timezone

from account.enums import SecretType
from account.forms import (
    LoginForm,
    SignupForm,
)
from account.models import Device, Secret
from common.integrations.postmark import client as postmark

logger = logging.getLogger(__name__)


def login(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect(to="profile")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            authed_user = form.cleaned_data["user"]
            device, created = Device.objects.get_or_create_from_request(request, authed_user)
            if device and device.blocked:
                messages.error(
                    request,
                    message="This device has been blocked. Please contact support.",
                )
                return redirect("login")
            if authed_user.mfa_enabled and (not device or not device.trusted):
                secret = Secret.objects.create(
                    user=authed_user,
                    secret_type=SecretType.TWO_FACTOR,
                )
                try:
                    postmark.send_email_template(
                        authed_user.email,
                        settings.POSTMARK_2FA_TEMPLATE_ID,
                        data={
                            "name": authed_user.first_name
                            if authed_user.first_name
                            else "Stranger",
                            "action_url": secret.magic_link,
                            "product_name": "Floret",
                            "operating_system": device.os_family if device else "Unknown",
                            "device_name": device.device_type if device else "Unknown Device",
                            "ip_address": device.ip_address if device else "Unknown",
                        },
                        tag="Application",
                    )
                    messages.info(
                        request,
                        message="A login link has been sent to your email address.",
                    )
                except Exception as e:
                    logger.error(f"Failed to send 2FA email: {e}")
                    messages.error(
                        request,
                        message="Failed to send two-factor authentication email.",
                    )
                    return redirect("login")
                return redirect("two_factor_notice")

            # Login successful - set cookie and redirect
            auth_login(request, form.cleaned_data["user"])
            next_url = request.GET.get("next", "profile")
            response = redirect(to=next_url)

            # Set device token cookie (1 year expiry)
            if device:
                response.set_cookie(
                    "device_token",
                    device.device_token,
                    max_age=365 * 24 * 60 * 60,  # 1 year
                    httponly=True,
                    secure=request.is_secure(),  # True in production with HTTPS
                    samesite="Lax",
                )
            else:
                # Clear any stale cookie for anonymous devices
                response.delete_cookie("device_token")

            return response
    else:
        form = LoginForm()

    return render(request, "login.html", context={"form": form})


def signup(request):
    """Handle new user registration."""
    if request.user.is_authenticated:
        return redirect(to="profile")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, message="Account created successfully!")
            if not user.email_verified_at:
                secret = Secret.objects.create(
                    user=user,
                    secret_type=SecretType.EMAIL_VERIFICATION,
                )
                try:
                    postmark.send_email_template(
                        user.email,
                        settings.POSTMARK_VERIFY_EMAIL_TEMPLATE_ID,
                        data={
                            "name": user.first_name if user.first_name else "Stranger",
                            "action_url": secret.magic_link,
                            "product_name": "Floret",
                        },
                        tag="Application",
                    )
                    messages.info(
                        request,
                        message="Please verify your email address to unlock all features.",
                    )
                except Exception as e:
                    logger.error(f"Failed to send verification email: {e}")

            return redirect(to="profile")
    else:
        form = SignupForm()

    return render(request, "signup.html", context={"form": form})


def logout(request):
    """Log the user out."""
    auth_logout(request)
    messages.success(request, message="You have been logged out.")
    return redirect(to="login")


def magic_link(request):
    """Passwordless authentication using temporary Secret.code"""
    code = request.GET.get("secret")
    now = timezone.now()
    next = "login"

    secret = Secret.objects.filter(
        code=code,
    ).first()
    error_message = None
    if not secret:
        error_message = "There was an error authenticating your account."
    elif secret.used_at:
        error_message = "Request has already been used."
    elif secret.expires_at < now:
        error_message = "Request has expired."
    if error_message:
        messages.error(request, message=error_message)
        return redirect(next)

    device, created = Device.objects.get_or_create_from_request(request, secret.user)

    # Mark device as trusted if it exists
    if device and not device.trusted:
        device.trusted = True
        device.save()

    auth_login(request, user=secret.user)
    secret.used_at = now
    secret.save()
    if not secret.user.email_verified_at:
        secret.user.email_verified_at = now
        secret.user.save()

    # Determine redirect based on secret type
    match secret.secret_type:
        case SecretType.PASSWORD_RESET:
            next = "password_reset"
        case SecretType.EMAIL_VERIFICATION:
            messages.success(request, message="Email successfully verified!")
            next = "profile"
        case SecretType.TWO_FACTOR:
            next = "profile"

    # Create response and set device token cookie
    response = redirect(next)
    if device:
        response.set_cookie(
            "device_token",
            device.device_token,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=True,
            secure=request.is_secure(),
            samesite="Lax",
        )
    else:
        # Clear any stale cookie for anonymous devices
        response.delete_cookie("device_token")

    return response
