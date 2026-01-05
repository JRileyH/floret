from django.urls import path

from .views import auth as auth_views
from .views import password_reset as password_reset_views
from .views import profile as profile_views
from .views import two_factor as two_factor_views

urlpatterns = [
    # auth
    path(route="login/", view=auth_views.login, name="login"),
    path(route="signup/", view=auth_views.signup, name="signup"),
    path(route="logout/", view=auth_views.logout, name="logout"),
    path(route="magic_link/", view=auth_views.magic_link, name="magic_link"),
    # profile
    path(route="profile/", view=profile_views.profile, name="profile"),
    path(route="update_profile/", view=profile_views.update_profile, name="update_profile"),
    # 2fa
    path(
        route="two_factor_notice/",
        view=two_factor_views.two_factor_notice,
        name="two_factor_notice",
    ),
    path("profile/devices/", two_factor_views.device_list, name="device_list"),
    path(
        "profile/devices/<uuid:device_id>/", two_factor_views.device_detail, name="device_detail"
    ),
    path(
        "profile/devices/<uuid:device_id>/trust/",
        two_factor_views.device_trust,
        name="device_trust",
    ),
    path(
        "profile/devices/<uuid:device_id>/block/",
        two_factor_views.device_block,
        name="device_block",
    ),
    path(
        "profile/devices/<uuid:device_id>/delete/",
        two_factor_views.device_delete,
        name="device_delete",
    ),
    path(
        "profile/ip/<uuid:ip_id>/toggle-block/",
        two_factor_views.ip_toggle_block,
        name="ip_toggle_block",
    ),
    # password reset
    path(
        route="password_reset/", view=password_reset_views.password_reset, name="password_reset"
    ),
    path(
        route="request_password_reset/",
        view=password_reset_views.request_password_reset,
        name="request_password_reset",
    ),
    path(
        route="password_reset_confirmation/",
        view=password_reset_views.password_reset_confirmation,
        name="password_reset_confirmation",
    ),
]
