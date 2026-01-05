import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# CORE SETTINGS
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = os.environ.get("BASE_URL", "http://localhost:9000")

# Environment configuration
ENV = os.environ.get("ENV", "prod")
VERSION = os.environ.get("GIT_SHA", "unset")
IS_PROD = ENV == "prod"
IS_LOCAL = ENV == "local"
IS_TESTING = ENV == "test"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-)8xbb+w(8n&=bef0_15b!jn#asg)ws*2v3dhrx@1_wfb%j2c&l",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not IS_PROD

# Parse ALLOWED_HOSTS from environment (comma-separated) or use defaults
_allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", None)
if _allowed_hosts_env is not None:
    # Environment variable is set, parse it
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts_env.split(",") if host.strip()]
else:
    # Use defaults for local development
    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
        "floret",  # Allow Prometheus to scrape metrics from within Docker network
    ]

INTERNAL_IPS = ["127.0.0.1"]

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

INTERNAL_APPS = [
    "floret",
    "account",
    "home",
    "theme",
]

VENDOR_APPS = [
    "django_prometheus",
    "django_htmx",
    "django_q",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = INTERNAL_APPS + VENDOR_APPS + DJANGO_APPS

# Development-only apps
if DEBUG:
    INSTALLED_APPS += ["django_extensions"]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "floret.middleware.request_logging.RequestLoggingMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "floret.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "account/templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "floret.wsgi.application"

# ==============================================================================
# VENDOR CONFIGURATION
# ==============================================================================
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        environment=ENV,
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.1,
        sample_rate=1.0,
    )

POSTMARK_API_KEY = os.environ.get("POSTMARK_API_KEY")
POSTMARK_EMAIL = os.environ.get("POSTMARK_EMAIL")
POSTMARK_API_URL = os.environ.get("POSTMARK_API_URL", "https://api.postmarkapp.com")
POSTMARK_2FA_TEMPLATE_ID = os.environ.get("POSTMARK_2FA_TEMPLATE_ID")
POSTMARK_VERIFY_EMAIL_TEMPLATE_ID = os.environ.get("POSTMARK_VERIFY_EMAIL_TEMPLATE_ID")
POSTMARK_PASSWORD_RESET_TEMPLATE_ID = os.environ.get("POSTMARK_PASSWORD_RESET_TEMPLATE_ID")

# ==============================================================================
# DATABASE
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# ==============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "HOST": os.environ.get("DB_HOST"),
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "PORT": os.environ.get("DB_PORT"),
        "TEST": {
            "NAME": "test_database",
        },
    },
}

# ==============================================================================
# CACHE
# https://docs.djangoproject.com/en/5.1/topics/cache/
# ==============================================================================

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
REDIS_PROTOCOL = "rediss" if IS_PROD else "redis"

# Build Redis URL with password if present
if REDIS_PASSWORD:
    REDIS_URL = f"{REDIS_PROTOCOL}://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
else:
    REDIS_URL = f"{REDIS_PROTOCOL}://{REDIS_HOST}:{REDIS_PORT}"

CACHES = {
    "default": {
        "BACKEND": "django_prometheus.cache.backends.redis.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

# ==============================================================================
# DJANGO-Q2 TASK QUEUE
# ==============================================================================

Q_CLUSTER = {
    "name": "floret",
    "redis": f"{REDIS_URL}/2",
    "timeout": 300,
    "retry": 600,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}

# ==============================================================================
# AUTHENTICATION
# https://docs.djangoproject.com/en/5.1/topics/auth/
# ==============================================================================

AUTH_USER_MODEL = "account.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGIN_URL = "/account/login/"
LOGIN_REDIRECT_URL = "/account/profile"
LOGOUT_REDIRECT_URL = "/account/login/"

# ==============================================================================
# INTERNATIONALIZATION
# https://docs.djangoproject.com/en/5.1/topics/i18n/
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "theme/static/"),
]

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
    if IS_PROD
    else "whitenoise.storage.CompressedStaticFilesStorage"
)

# ==============================================================================
# MEDIA FILES
# ==============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ==============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ==============================================================================

# Note: BaseModel uses UUIDField as primary key, but this setting affects
# Django's internal models (contenttypes, sessions, etc.)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# LOGGING
# ==============================================================================
# Structured JSON logging for easy parsing by Loki/Grafana Alloy
# In production, logs are shipped to Grafana Cloud Loki
# In local dev, logs are shipped to local Loki instance


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "console": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "filters": {
        "skip_metrics": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: "/metrics" not in record.getMessage(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if not DEBUG else "console",
            "filters": ["skip_metrics"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",  # Default: only warnings/errors for all libraries
    },
    "loggers": {
        # Your application - log INFO and above
        "account": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "floret": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Request logging with IP/user agent (for traffic analysis)
        "floret.requests": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Django errors only (4xx/5xx responses)
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
