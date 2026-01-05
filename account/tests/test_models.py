import pytest

from account.models import User


@pytest.mark.django_db
class TestUserModel:
    """Test the custom User model."""

    def test_create_user(self):
        """Test creating a user with email and password."""
        user = User.objects.create_user(email="test@example.com", password="testpass123")

        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(email="admin@example.com", password="adminpass123")

        assert admin.email == "admin@example.com"
        assert admin.is_active
        assert admin.is_staff
        assert admin.is_superuser

    def test_email_is_normalized(self):
        """Test that email addresses are normalized (lowercased)."""
        user = User.objects.create_user(email="Test@EXAMPLE.com", password="testpass123")

        assert user.email == "test@example.com"

    def test_user_str_representation(self):
        """Test the string representation of a user."""
        user = User.objects.create_user(email="test@example.com", password="testpass123")

        assert str(user) == "test@example.com"

    def test_user_email_is_unique(self):
        """Test that duplicate emails are not allowed."""
        User.objects.create_user(email="test@example.com", password="testpass123")

        # Attempting to create another user with the same email should raise an error
        with pytest.raises(Exception):
            User.objects.create_user(email="test@example.com", password="anotherpass")


@pytest.mark.django_db
class TestUserQuerySet:
    """Test custom queryset methods (if you add any)."""

    def test_active_users(self):
        """Example: Test filtering active users."""
        User.objects.create_user(email="active@example.com", password="pass123")
        inactive_user = User.objects.create_user(email="inactive@example.com", password="pass123")
        inactive_user.is_active = False
        inactive_user.save()

        active_users = User.objects.filter(is_active=True)

        assert active_users.count() == 1
        assert active_users.first().email == "active@example.com"
