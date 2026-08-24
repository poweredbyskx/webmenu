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
    "/choose-venue/", "/set-venue/",
)

# menu.urls целиком обёрнуты в i18n_patterns() (см. config/urls.py) —
# реальные пути выглядят как /ru/api/..., /en/menu/ и т.д. Сравнивать нужно
# путь БЕЗ языкового префикса, иначе ни один префикс из списка выше не
# совпадёт ни разу (а /admin/, /static/, /media/, /i18n/, /sitemap.xml
# зарегистрированы вне i18n_patterns и всегда идут без префикса).
_LANGUAGE_CODES = {code for code, _ in settings.LANGUAGES}

# ВРЕМЕННО: пока меню kakao_gaudan наполняется контентом, по умолчанию
# незаметно подставляем старую точку (Мир 4), а не заставляем выбирать —
# сменить точку можно вручную через клик по логотипу (-> /choose-venue/).
# Убрать/заменить, когда появится финальный UX выбора точки.
DEFAULT_VENUE_SLUG = "kakao_mir4"


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
            if not slug:
                slug = DEFAULT_VENUE_SLUG
                request.session["venue_slug"] = slug
            # выбранная точка (в т.ч. дефолтная) могла быть деактивирована —
            # сбросить сессию и отправить на выбор, а не тихо падать/показывать пусто
            if not Venue.objects.filter(slug=slug, is_active=True).exists():
                del request.session["venue_slug"]
                return redirect(reverse("select_venue") + f"?next={request.path}")
        return self.get_response(request)
