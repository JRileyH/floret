from django.db import models


class SecretType(models.TextChoices):
    PASSWORD_RESET = "password_reset", "Password Reset"
    EMAIL_VERIFICATION = "email_verification", "Email Verification"
    TWO_FACTOR = "two_factor", "Two Factor Auth"
