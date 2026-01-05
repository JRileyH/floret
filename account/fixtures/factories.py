from __future__ import annotations

import factory
from factory.django import DjangoModelFactory

from account.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    password = factory.PostGenerationMethodCall("set_password", "password123")

    is_active = True
    is_staff = False
    is_superuser = False
