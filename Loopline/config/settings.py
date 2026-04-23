import dj_database_url
from pathlib import Path
import os
from dotenv import load_dotenv

# BASE_DIR is C:\nxtturn\Loopline
BASE_DIR = Path(__file__).resolve().parent.parent

# Look for .env in the Project Root (C:\nxtturn\.env)
# This file is ONLY used locally and is NOT pushed to Git.
load_dotenv(dotenv_path=BASE_DIR.parent / ".env")

# --- SMART ENVIRONMENT DETECTION (Crucial for all environments) ---
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"  # True for local, Dev Cloud, Test/QA
IS_LOCAL = os.getenv("IS_LOCAL", "False").lower() == "true"  # For entrypoint.sh logic

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = not IS_PRODUCTION  # DEBUG is only TRUE if NOT in production
if not IS_PRODUCTION and not SECRET_KEY:
    SECRET_KEY = "a-dummy-secret-key-for-local-development-only-do-not-use-in-prod"

# --- SMART ALLOWED_HOSTS (Reads from root .env or defaults) ---
raw_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [host.strip() for host in raw_hosts.split(",") if host.strip()]
if not IS_PRODUCTION:  # Only allow wildcard for local dev/testing
    ALLOWED_HOSTS.append("*")

# --- SMART FRONTEND URL (Reads from root .env or defaults) ---
# This is the PRIMARY URL the backend uses to build links (emails, password resets)
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://localhost:5173")

# --- INSTALLED APPS (Conditional for test utilities) ---
INSTALLED_APPS = [
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "anymail",
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    "corsheaders",
    "django_extensions",
    "community.apps.CommunityConfig",
    "allauth.socialaccount.providers.google",
]
# Only add e2e_test_utils if we're NOT in production
# This physically removes test apps from production builds
if not IS_PRODUCTION:
    INSTALLED_APPS.append("e2e_test_utils")

SITE_ID = 1

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "community.middleware.CypressTestMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# --- SMART DATABASE CONFIGURATION ---
if os.getenv("DATABASE_URL"):
    # If we are in Docker (Local or Cloud)
    # We ONLY require SSL if the environment is strictly 'production'
    DATABASES = {
        "default": dj_database_url.config(conn_max_age=600, ssl_require=IS_PRODUCTION)
    }
else:  # Fallback for local Windows-native development (not used with Docker)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = "en-us", "UTC", True, True

# 1. Folders for files (Static = CSS/JS, Media = User Uploads)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# 2. The "Switch" Logic (Laptop vs Cloud)
if IS_LOCAL:
    # Use your laptop's hard drive
    MEDIA_URL = "/media/"
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
else:
    # Use Google Cloud (We will set GS_BUCKET_NAME in the Google Console later)
    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"
    STORAGES = {
        "default": {"BACKEND": "storages.backends.gcloud.GoogleCloudStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- EMAIL CONFIGURATION (Conditional for tests) ---
EMAIL_MODE = os.getenv("EMAIL_MODE", "console")
DEFAULT_FROM_EMAIL = "nxtturn <noreply@nxtturn.com>"
SERVER_EMAIL = "admin@nxtturn.com"

# Force Memory Backend if in Test Mode (CRITICAL for Cypress `get_last_email` calls)
if os.getenv("CYPRESS_TESTING", "false").lower() == "true":
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
elif EMAIL_MODE == "brevo":
    EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    # Capture the key and immediately remove any invisible spaces or newlines
    raw_brevo_key = os.getenv("BREVO_API_KEY", "")
    ANYMAIL = {"BREVO_API_KEY": raw_brevo_key.strip()}
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ACCOUNT_CONFIRM_EMAIL_ON_GET = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": ["rest_framework.filters.SearchFilter"],
}

AUTHENTICATION_BACKENDS = (
    "allauth.account.auth_backends.AuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
)

ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "community.adapters.NxtTurnAccountAdapter"
SOCIALACCOUNT_ADAPTER = "community.adapters.NxtTurnSocialAccountAdapter"

# --- DJANGO-ALLAUTH Modern Settings ---
# These are the updated names for settings to remove UserWarnings
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True

REST_AUTH = {
    "USE_SESSION_AUTH": False,
    "SESSION_LOGIN": False,
    "USER_DETAILS_SERIALIZER": "community.serializers.UserSerializer",
    "REGISTER_SERIALIZER": "community.serializers.CustomRegisterSerializer",
    "LOGIN_SERIALIZER": "community.serializers.CustomLoginSerializer",
    "PASSWORD_RESET_CONFIRM_SERIALIZER": "community.serializers.CustomPasswordResetConfirmSerializer",
    "PASSWORD_RESET_SERIALIZER": "community.serializers.CustomPasswordResetRequestSerializer",
    "PASSWORD_RESET_CONFIRM_URL": f"{FRONTEND_URL}/auth/reset-password/{{uid}}/{{token}}/",
    "SIGNUP_FIELDS": {"username": {"required": True}, "email": {"required": True}},
}

# --- SMART SECURITY ROUTING (CORS & CSRF) ---
CORS_ALLOWED_ORIGINS = []
CSRF_TRUSTED_ORIGINS = []

if FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)
    CSRF_TRUSTED_ORIGINS.append(FRONTEND_URL)

# NEW: Also trust the Backend's own URL for Admin logins
BACKEND_URL = os.getenv("BACKEND_URL")
if BACKEND_URL:
    CSRF_TRUSTED_ORIGINS.append(BACKEND_URL)

# Always trust standard local addresses for convenience
extra_origins = ["https://localhost:5173", "https://127.0.0.1:5173"]
for origin in extra_origins:
    if origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(origin)
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.getenv("REDIS_URL", "redis://redis:6379/0")]},
    },
}

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online", "prompt": "select_account"},
        "JWT_LEEWAY": 600,
    }
}

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "optional"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"  # Force HTTPS for email links

# Ensure a 10-minute buffer for all social account tokens
SOCIALACCOUNT_JWT_LEEWAY = 600

# ==============================================================================
# --- INDUSTRY STANDARD SELF-HEALING ARCHITECTURE ---
# This block ensures the 'Site' record always matches your current laptop IP.
# ==============================================================================
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def sync_production_settings(sender, **kwargs):
    # Automatically fix the 'Site' domain (so email links point to your current IP)
    if sender.name == "django.contrib.sites":
        from django.contrib.sites.models import Site

        new_domain = (
            FRONTEND_URL.replace("https://", "").replace("http://", "").strip("/")
        )
        Site.objects.update_or_create(
            id=SITE_ID, defaults={"domain": new_domain, "name": "nxtturn.com"}
        )


# Password reset links will now expire after 1 hour (3600 seconds)
PASSWORD_RESET_TIMEOUT = 3600
