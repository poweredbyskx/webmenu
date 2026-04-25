"""
Django settings for config project.
Prod-ready: все секреты и окружение-зависимые настройки — через .env
"""

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# --- .env ---------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),  # по умолчанию False — безопаснее
)
# Читаем .env, если он есть (в проде .env тоже рядом, в dev — тоже)
environ.Env.read_env(BASE_DIR / ".env")

# --- Core ---------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")  # упадёт, если не задан — это правильно
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# --- Apps ---------------------------------------------------------------
INSTALLED_APPS = [
    "jazzmin",
    "modeltranslation",  # ВАЖНО: должен быть ПЕРЕД django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third-party
    "adminsortable2",
    "imagekit",

    # local
    "menu.apps.MenuConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "menu.context_processors.menu_categories",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -----------------------------------------------------------
# DATABASE_URL формата: postgres://user:password@host:5432/dbname
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
# Держим соединение живым 60 секунд (снижает латентность)
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# --- Password validation ------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n ---------------------------------------------------------------
LANGUAGE_CODE = "ru"
USE_I18N = True
USE_TZ = True
TIME_ZONE = "Asia/Ashgabat"  # поставь свою таймзону, если нужна другая

LANGUAGES = [("ru", "Русский"), ("en", "English"), ("tk", "Türkmençe")]
LOCALE_PATHS = [BASE_DIR / "locale"]

MODELTRANSLATION_LANGUAGES = ("ru", "en", "tk")
MODELTRANSLATION_DEFAULT_LANGUAGE = "ru"

# --- Static & media -----------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# WhiteNoise: сжатые + хэшированные имена файлов (долгий кеш)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Security (prod) ----------------------------------------------------
# За nginx-прокси Django должен узнать, что запрос пришёл по HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # включишь, когда будешь уверен
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

# --- Logging ------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# --- Jazzmin ------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "Админ",
    "site_header": "Какао",
    "site_brand": "Какао",
    "welcome_sign": "Добро пожаловать",
    "copyright": "Кофе и Завтраки",
    "navigation_expanded": False,
    "show_ui_builder": False,
    "topmenu_links": [
        {"name": "Перейти на Сайт", "url": "/", "icon": "fas fa-home", "new_window": False},
    ],
    "usermenu_links": [
        {"name": "Перейти на сайт", "url": "/", "icon": "fas fa-home", "new_window": False},
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": True,
    "body_small_text": True,
    "sidebar_nav_small_text": True,
    "sidebar_disable_expand": True,
    "sidebar_nav_compact_style": True,
    "navbar": "navbar-white navbar-light",
    "sidebar": "sidebar-light-primary",
    "accent": "accent-maroon",
}