import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from account.forms import (
    ProfileUpdateForm,
)

logger = logging.getLogger(__name__)


@login_required
def profile(request):
    """Display user profile."""
    return render(request, "profile.html", context={"user": request.user})


@login_required
def update_profile(request):
    """Handle profile updates."""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, message="You have successfully updated your user info.")
            return redirect(to="profile")
    else:
        form = ProfileUpdateForm(user=request.user)

    return render(request, "form.html", context={"form": form, "user": request.user})
