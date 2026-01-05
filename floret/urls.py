from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("account/", include("account.urls")),
    path("", include("django_prometheus.urls")),
    # Serve robots.txt from project root
    re_path(
        r"^robots\.txt$",
        serve,
        {"path": "robots.txt", "document_root": settings.BASE_DIR},
    ),
    path("", include("home.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]
