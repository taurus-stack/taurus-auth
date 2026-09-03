"""
Django settings for taurus_auth project.
"""

from pathlib import Path
import os
from datetime import timedelta

from django.core.exceptions import ImproperlyConfigured

import pymysql

# Print environment variables for debugging
# print("=" * 60)
# print("Taurus Auth environment variable check:")
# print(f"DB_ENGINE: {os.getenv('DB_ENGINE', 'not set')}")
# print(f"DB_NAME: {os.getenv('DB_NAME', 'not set')}")
# print(f"DB_USER: {os.getenv('DB_USER', 'not set')}")
# print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD', 'not set')}")
# print(f"DB_HOST: {os.getenv('DB_HOST', 'not set')}")
# print(f"DB_PORT: {os.getenv('DB_PORT', 'not set')}")
# print(f"REDIS_URL: {os.getenv('REDIS_URL', 'not set')}")
# print(f"BACKEND_JWT_SECRET: {os.getenv('BACKEND_JWT_SECRET', 'not set')}")
# print(f"ALLOWED_BACKEND_IPS: {os.getenv('ALLOWED_BACKEND_IPS', 'not set')}")
# print("=" * 60)

pymysql.version_info = (1, 4, 13, "final", 0)
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-this-in-production")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]


def _require_env_secret(env_var: str, default: str) -> str:
    """Must be set via environment variable in non-DEBUG mode, raises ImproperlyConfigured otherwise"""
    value = os.getenv(env_var, default)
    if value == default and not DEBUG:
        raise ImproperlyConfigured(
            f"Security setting: {env_var} must be set via environment variable in production (DEBUG=False), "
            f"currently using insecure default value"
        )
    return value

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "ticket",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "ticket.middleware.SecurityMiddleware",
]

ROOT_URLCONF = "taurus_auth.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "taurus_auth.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.getenv("DB_NAME", "taurus_auth"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", "123456"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "3306"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("BACKEND_JWT_EXPIRES_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": _require_env_secret("BACKEND_JWT_SECRET", "your-jwt-secret-key-change-in-production"),
    "VERIFYING_KEY": _require_env_secret("BACKEND_JWT_SECRET", "your-jwt-secret-key-change-in-production"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

ALLOWED_BACKEND_IPS = os.getenv("ALLOWED_BACKEND_IPS", "").split(",")
ALLOWED_BACKEND_IPS = [ip.strip() for ip in ALLOWED_BACKEND_IPS if ip.strip()]

RATELIMIT_ENABLE = os.getenv("RATELIMIT_ENABLE", "True").lower() == "true"
RATELIMIT_RATE = os.getenv("RATELIMIT_RATE", "100/m")

MACAROON_ROOT_KEY = _require_env_secret("MACAROON_ROOT_KEY", "taurus_macaroon_root_key_change_in_production")

BACKEND_SERVICE_TOKEN = _require_env_secret("BACKEND_SERVICE_TOKEN", "backend_token_change_in_production")

TICKET_DEFAULT_EXPIRES_MINUTES = int(os.getenv("TICKET_DEFAULT_EXPIRES_MINUTES", "5"))

TICKET_MAX_EXPIRES_MINUTES = int(os.getenv("TICKET_MAX_EXPIRES_MINUTES", "60"))

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "taurus_auth.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "ticket": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

os.makedirs(BASE_DIR / "logs", exist_ok=True)