from typing import Any

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from account.enums import SecretType
from account.models import Secret, User
from common.mixins.forms import BaseForm


class LoginForm(BaseForm):
    """Form for user login with email and password."""

    form_title = "Log In"
    submit_text = "Log In"

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "your@email.com",
                "class": "input input-bordered w-full",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "class": "input input-bordered w-full",
            }
        )
    )

    def clean(self) -> dict:
        cleaned_data = super().clean() or {}
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            if not User.objects.filter(email=email).exists():
                self.add_error("email", f"User {email} could not be found.")
            else:
                user = authenticate(username=email, password=password)
                if user is None:
                    self.add_error("password", "Invalid email or password.")
                else:
                    cleaned_data["user"] = user

        return cleaned_data


class SignupForm(BaseForm):
    """Form for new user registration."""

    form_title = "Sign Up"
    submit_text = "Sign Up"

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "your@email.com",
                "class": "input input-bordered w-full",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "class": "input input-bordered w-full",
            }
        )
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "class": "input input-bordered w-full",
            }
        ),
    )

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password and settings.IS_PROD:
            try:
                validate_password(password, user=None)
            except DjangoValidationError as e:
                raise forms.ValidationError(list(e.messages))
        return password

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self) -> dict[str, Any] | None:
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")

        return cleaned_data

    def save(self) -> User:
        """Create and return the new user."""
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
        )


class ProfileUpdateForm(BaseForm):
    """Form for updating user profile information."""

    form_title = "Update User Info"
    submit_text = "Update"
    cancel_url = "profile"

    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "First Name...",
                "class": "input input-bordered w-full",
            }
        ),
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last Name...",
                "class": "input input-bordered w-full",
            }
        ),
    )
    mfa_enabled = forms.BooleanField(
        required=False,
        label="Enable Two-Factor Authentication",
        widget=forms.CheckboxInput(
            attrs={
                "class": "checkbox checkbox-primary",
            }
        ),
    )

    def __init__(self, *args, user: User, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        # Pre-populate with current user data
        if not self.is_bound:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["mfa_enabled"].initial = user.mfa_enabled

    def save(self) -> User:
        """Update and return the user."""
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.mfa_enabled = self.cleaned_data["mfa_enabled"]
        self.user.save()
        return self.user


class PasswordResetForm(BaseForm):
    """Form to update password for user."""

    form_title = "Update Password"
    submit_text = "Update"

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "class": "input input-bordered w-full",
            }
        )
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "class": "input input-bordered w-full",
            }
        ),
    )

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password and settings.IS_PROD:
            try:
                validate_password(password, user=None)
            except DjangoValidationError as e:
                raise forms.ValidationError(list(e.messages))
        return password

    def clean(self) -> dict[str, Any] | None:
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")

        return cleaned_data


class RequestPasswordResetForm(BaseForm):
    """Form for requesting a password reset email."""

    form_title = "Request Password Reset"
    submit_text = "Request"
    cancel_url = "login"

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "your@email.com",
                "class": "input input-bordered w-full",
            }
        )
    )

    def clean(self) -> dict:
        cleaned_data = super().clean() or {}
        email = cleaned_data.get("email")
        if not email:
            return cleaned_data

        user = User.objects.filter(email=email).first()
        if not user:
            cleaned_data["secret"] = None
            return cleaned_data
        secret = Secret.objects.filter(
            user=user,
            secret_type=SecretType.PASSWORD_RESET,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()
        if not secret:
            secret = Secret.objects.create_for_password_reset(user)
        cleaned_data["secret"] = secret

        return cleaned_data
