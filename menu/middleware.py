import time

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from .models import Venue

# Middleware реализован через __call__, поэтому request.resolver_match ещё
# не установлен на момент проверки — Django резолвит URL только внутри
# цепочки get_response(), глубже текущей мидлвари. Поэтому исключения —
# строго по префиксу пути, не по имени URL.
VENUE_EXEMPT_PATHS_PREFIXES = (
    "/static/", "/media/", "/admin/", "/api/", "/i18n/", "/sitemap.xml",
    "/choose-venue/", "/set-venue/", "/admin-tools/",
)

# menu.urls целиком обёрнуты в i18n_patterns() (см. config/urls.py) —
# реальные пути выглядят как /ru/api/..., /en/menu/ и т.д. Сравнивать нужно
# путь БЕЗ языкового префикса, иначе ни один префикс из списка выше не
# совпадёт ни разу (а /admin/, /static/, /media/, /i18n/, /sitemap.xml
# зарегистрированы вне i18n_patterns и всегда идут без префикса).
_LANGUAGE_CODES = {code for code, _ in settings.LANGUAGES}

# Выбор точки живёт сутки — по истечении срока сайт снова спросит, какое
# кафе показывать. Клик по логотипу к выбору точки больше не ведёт (это
# теперь обычная ссылка на главную) — до появления отдельной кнопки смены
# локации внутри сайта единственный способ увидеть карточку раньше срока —
# истечение суток или очистка cookies.
VENUE_SESSION_TTL_SECONDS = 24 * 60 * 60


def _strip_locale_prefix(path):
    segments = path.split("/", 2)
    if len(segments) > 1 and segments[1] in _LANGUAGE_CODES:
        return "/" + segments[2] if len(segments) > 2 else "/"
    return path


class VenueSelectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = _strip_locale_prefix(request.path)
        if not path.startswith(VENUE_EXEMPT_PATHS_PREFIXES):
            slug = request.session.get("venue_slug")
            set_at = request.session.get("venue_set_at")
            expired = set_at is None or (time.time() - set_at) > VENUE_SESSION_TTL_SECONDS

            if not slug or expired:
                request.session.pop("venue_slug", None)
                request.session.pop("venue_set_at", None)
                return redirect(reverse("select_venue") + f"?next={request.path}")
            # выбранная точка могла быть деактивирована — сбросить сессию и
            # отправить на выбор, а не тихо падать/показывать пусто
            if not Venue.objects.filter(slug=slug, is_active=True).exists():
                request.session.pop("venue_slug", None)
                request.session.pop("venue_set_at", None)
                return redirect(reverse("select_venue") + f"?next={request.path}")
        return self.get_response(request)
