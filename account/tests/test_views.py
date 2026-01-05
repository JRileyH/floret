import pytest
from django.urls import reverse

from account.models import User


@pytest.mark.django_db
class TestLoginView:
    """Test the login view and authentication."""

    def test_login_page_loads(self, client):
        """Test that the login page loads successfully."""
        response = client.get(reverse("login"))

        assert response.status_code == 200
        assert "login.html" in [t.name for t in response.templates]

    def test_successful_login(self, client):
        """Test logging in with valid credentials."""
        # Create a test user
        User.objects.create_user(email="test@example.com", password="testpass123")

        # Attempt login
        response = client.post(
            reverse("login"), {"email": "test@example.com", "password": "testpass123"}
        )

        # Should redirect to profile
        assert response.status_code == 302
        assert response.url == reverse("profile")

    def test_login_with_invalid_credentials(self, client):
        """Test login fails with invalid credentials."""
        User.objects.create_user(email="test@example.com", password="testpass123")

        response = client.post(
            reverse("login"), {"email": "test@example.com", "password": "wrongpassword"}
        )

        # Should stay on login page with error message
        assert response.status_code == 200
        assert "Invalid email or password" in str(response.content)

    def test_login_with_missing_email(self, client):
        """Test login validation with missing email."""
        response = client.post(reverse("login"), {"email": "", "password": "testpass123"})

        assert response.status_code == 200
        # Django Forms puts errors in form.email.errors
        form = response.context["form"]
        assert "email" in form.errors

    def test_login_with_missing_password(self, client):
        """Test login validation with missing password."""
        response = client.post(reverse("login"), {"email": "test@example.com", "password": ""})

        assert response.status_code == 200
        form = response.context["form"]
        assert "password" in form.errors

    def test_authenticated_user_redirected_from_login(self, client, sample_user):
        """Test that authenticated users are redirected away from login page."""
        client.force_login(sample_user)

        response = client.get(reverse("login"))

        assert response.status_code == 302
        assert response.url == reverse("profile")

    def test_login_preserves_form_data_on_error(self, client):
        """Test that email is preserved when validation fails."""
        response = client.post(reverse("login"), {"email": "test@example.com", "password": ""})

        # Django Forms preserve input data in form.data
        form = response.context["form"]
        assert form.data.get("email") == "test@example.com"


@pytest.mark.django_db
class TestSignupView:
    """Test the signup view and user registration."""

    def test_signup_page_loads(self, client):
        """Test that the signup page loads successfully."""
        response = client.get(reverse("signup"))

        assert response.status_code == 200
        assert "signup.html" in [t.name for t in response.templates]

    def test_successful_signup(self, client):
        """Test creating a new account."""
        response = client.post(
            reverse("signup"),
            {
                "email": "newuser@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
            },
        )

        # Should redirect to profile
        assert response.status_code == 302
        assert response.url == reverse("profile")

        # User should exist and be logged in
        user = User.objects.get(email="newuser@example.com")
        assert user is not None
        assert user.is_active

    def test_signup_with_mismatched_passwords(self, client):
        """Test signup fails when passwords don't match."""
        response = client.post(
            reverse("signup"),
            {
                "email": "newuser@example.com",
                "password": "testpass123",
                "password_confirm": "differentpass",
            },
        )

        assert response.status_code == 200
        assert "Passwords do not match" in str(response.content)
        assert not User.objects.filter(email="newuser@example.com").exists()

    def test_signup_with_existing_email(self, client, sample_user):
        """Test signup fails when email already exists."""
        response = client.post(
            reverse("signup"),
            {
                "email": sample_user.email,
                "password": "testpass123",
                "password_confirm": "testpass123",
            },
        )

        assert response.status_code == 200
        assert "An account with this email already exists" in str(response.content)

    def test_signup_with_missing_fields(self, client):
        """Test signup validation with missing required fields."""
        response = client.post(
            reverse("signup"), {"email": "", "password": "", "password_confirm": ""}
        )

        assert response.status_code == 200
        # Django Forms shows "This field is required." for required fields
        form = response.context["form"]
        assert "email" in form.errors
        assert "password" in form.errors


@pytest.mark.django_db
class TestLogoutView:
    """Test the logout functionality."""

    def test_logout(self, authenticated_client):
        """Test logging out."""
        response = authenticated_client.get(reverse("logout"))

        # Should redirect to home
        assert response.status_code == 302
        assert response.url == "/account/login/"

    def test_logout_without_authentication(self, client):
        """Test that unauthenticated users can still access logout."""
        response = client.get(reverse("logout"))

        # Should still redirect (even if not logged in)
        assert response.status_code == 302


@pytest.mark.django_db
class TestProfileView:
    """Test the user profile view."""

    def test_profile_requires_authentication(self, client):
        """Test that profile page requires login."""
        response = client.get(reverse("profile"))

        # Should redirect to login with 'next' parameter
        assert response.status_code == 302
        assert reverse("login") in response.url

    def test_profile_loads_for_authenticated_user(self, authenticated_client, sample_user):
        """Test that authenticated users can access their profile."""
        response = authenticated_client.get(reverse("profile"))

        assert response.status_code == 200
        assert "profile.html" in [t.name for t in response.templates]
        assert response.context["user"] == sample_user

    def test_profile_displays_user_email(self, authenticated_client, sample_user):
        """Test that profile displays the user's email."""
        response = authenticated_client.get(reverse("profile"))

        assert sample_user.email in str(response.content)


# ==============================================================================
# Example: Testing with different user states
# ==============================================================================


@pytest.mark.django_db
class TestAuthenticationStates:
    """Examples of testing different authentication states."""

    def test_anonymous_user(self, client):
        """Test behavior for anonymous (not logged in) users."""
        response = client.get(reverse("profile"))
        assert response.status_code == 302  # Redirected to login

    def test_regular_user(self, authenticated_client):
        """Test behavior for regular authenticated users."""
        response = authenticated_client.get(reverse("profile"))
        assert response.status_code == 200

    def test_superuser(self, client, sample_superuser):
        """Test behavior for superusers."""
        client.force_login(sample_superuser)
        response = client.get(reverse("profile"))
        assert response.status_code == 200
        assert response.context["user"].is_superuser
