import pytest

from account.models import User


@pytest.fixture
def sample_user():
    return User.objects.create_user(email="sample@example.com", password="testpass123")


@pytest.fixture
def sample_superuser():
    return User.objects.create_superuser(email="admin@example.com", password="adminpass123")


@pytest.fixture
def authenticated_client(client, sample_user):
    client.force_login(sample_user)
    return client
