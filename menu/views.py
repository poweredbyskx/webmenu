import logging
import time

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView, TemplateView
from django_ratelimit.decorators import ratelimit

from .models import Category, Item, RoastedCoffee, Venue


logger = logging.getLogger(__name__)

# Минимальная длина запроса — отсекает "а", "б" и пустые строки
MIN_QUERY_LEN = 2

# Поля, по которым ищем (все языки + категория)
SEARCH_FIELDS = [
    "name", "name_ru", "name_en", "name_tk",
    "description", "description_ru", "description_en", "description_tk",
    "category__name", "category__name_ru", "category__name_en", "category__name_tk",
]


def build_search_queryset(query: str, venue_slug: str | None = None):
    """
    Возвращает QuerySet items, отфильтрованный по подстроке в любом из языковых
    полей или в названии категории. Регистронезависимо (icontains = ILIKE в Postgres).
    Если передан venue_slug — дополнительно ограничивает точкой.
    """
    q = (query or "").strip()
    if len(q) < MIN_QUERY_LEN:
        return Item.objects.none()

    filters = Q()
    for field in SEARCH_FIELDS:
        filters |= Q(**{f"{field}__icontains": q})

    qs = Item.objects.filter(filters, is_active=True)
    if venue_slug:
        qs = qs.filter(category__venues__slug=venue_slug)

    return (
        qs
        .select_related("category")
        .distinct()
        .order_by("category__order", "order", "name")
    )


DRINK_CATEGORY_SLUGS = ['non_coffee', 'ice_coffee', 'cocktails']


def _require_venue_param(request):
    """
    Общая проверка для api_*: venue обязателен, чтобы старый/необновлённый
    клиент явно получал ошибку, а не смешанные данные нескольких точек.
    Возвращает (venue_slug, None) или (None, JsonResponse с 400).
    """
    venue_slug = request.GET.get("venue")
    if not venue_slug:
        return None, JsonResponse({"error": "Query param 'venue' is required"}, status=400)
    return venue_slug, None

class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        venue_slug = self.request.session.get("venue_slug")
        categories = (
            Category.objects.filter(venues__slug=venue_slug)
            .distinct()
            .prefetch_related("items")
        )
        first_category = categories.first()

        DRINK_SLUGS = ['non_coffee', 'ice_coffee', 'cocktails']
        base_items = Item.objects.filter(is_active=True, category__venues__slug=venue_slug)

        seasonal_food = list(
            base_items.filter(is_seasonal=True)
            .exclude(category__slug__in=DRINK_SLUGS)
            .select_related("category")[:6]
        )
        seasonal_drinks = list(
            base_items.filter(is_seasonal=True, category__slug__in=DRINK_SLUGS)
            .select_related("category")[:6]
        )

        new_food = list(
            base_items.filter(is_new=True)
            .exclude(category__slug__in=DRINK_SLUGS)
            .select_related("category")[:6]
        )
        new_drinks = list(
            base_items.filter(is_new=True, category__slug__in=DRINK_SLUGS)
            .select_related("category")[:6]
        )

        ctx["seasonal_food"] = seasonal_food
        ctx["seasonal_drinks"] = seasonal_drinks
        ctx["new_food"] = new_food
        ctx["new_drinks"] = new_drinks
        ctx["categories"] = categories
        ctx["menu_items"] = (
            first_category.items.filter(is_active=True) if first_category else Item.objects.none()
        )
        ctx["active_category"] = first_category

        return ctx


class MenuView(TemplateView):
    template_name = "pages/menu.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        venue_slug = self.request.session.get("venue_slug")
        categories = (
            Category.objects.filter(venues__slug=venue_slug)
            .distinct()
            .order_by("order", "name")
        )
        items = (
            Item.objects.filter(is_active=True, category__venues__slug=venue_slug)
            .select_related("category")
            .order_by("category__order", "order", "name")
        )
        first_category = categories.first()

        ctx["categories"] = categories
        ctx["items"] = items
        ctx["active_category"] = first_category

        return ctx


class CategoryView(ListView):
    model = Item
    template_name = "pages/category.html"
    context_object_name = "items"

    def dispatch(self, request, *args, **kwargs):
        venue_slug = request.session.get("venue_slug")
        self.category = get_object_or_404(
            Category, slug=self.kwargs["slug"], venues__slug=venue_slug
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Item.objects.filter(category=self.category, is_active=True)
            .select_related("category")
            .order_by("order", "name")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category"] = self.category
        return ctx


class SearchView(ListView):
    model = Item
    template_name = "pages/search.html"
    context_object_name = "items"
    paginate_by = 20  # пагинация, чтобы при большом меню не вываливать всё сразу

    def get_queryset(self):
        self.q = (self.request.GET.get("q") or "").strip()
        venue_slug = self.request.session.get("venue_slug")
        return build_search_queryset(self.q, venue_slug)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = getattr(self, "q", "")
        ctx["min_query_len"] = MIN_QUERY_LEN
        return ctx


@ratelimit(key="ip", rate="30/m", block=True)
def search_api(request):
    """
    JSON-эндпоинт для живого поиска с фронта.
    Возвращает максимум 10 результатов.
    Лимит: 30 запросов в минуту с одного IP (django-ratelimit),
    при превышении отвечает 403.
    """
    q = (request.GET.get("q") or "").strip()

    if len(q) < MIN_QUERY_LEN:
        return JsonResponse([], safe=False)

    venue_slug = request.session.get("venue_slug")
    qs = list(build_search_queryset(q, venue_slug)[:10])

    logger.info("search_api query=%r results=%d", q, len(qs))

    data = [
        {
            "name": item.name,
            "price": str(item.price),
            "image": item.thumb_300.url if item.image else "",
            "category": item.category.name,
            "category_slug": item.category.slug,
            "item_slug": item.slug,
        }
        for item in qs
    ]

    return JsonResponse(data, safe=False)


class RoastedView(TemplateView):
    template_name = "pages/roasted.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["coffees"] = RoastedCoffee.objects.filter(is_active=True)
        ctx["nitro"] = Item.objects.filter(slug="nitro_coffee", is_active=True).select_related("category").first()
        ctx["cold_brew"] = Item.objects.filter(
            slug="cold_brew", is_active=True
        ).select_related("category").first()
        return ctx
    

class BeansView(TemplateView):
    template_name = "pages/beans.html"


def select_venue(request):
    venues = Venue.objects.filter(is_active=True)
    return render(
        request,
        "pages/select_venue.html",
        {"venues": venues, "next": request.GET.get("next", "/")},
    )


def set_venue(request, slug):
    venue = get_object_or_404(Venue, slug=slug, is_active=True)
    request.session["venue_slug"] = venue.slug
    request.session["venue_set_at"] = time.time()
    next_url = request.GET.get("next") or "/"
    # next — параметр из query string, без проверки это open redirect
    # (?next=https://evil.com увёл бы пользователя с доверенного домена)
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"
    return redirect(next_url)


def download_apk(request):
    """
    Раздача свежего APK планшетам через сайт вместо ручной передачи файла.
    Доступ только staff — иначе 403, без утечки, существует ли файл вообще.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponseForbidden()

    apk_path = settings.APK_RELEASES_DIR / "KAKAO.apk"
    if not apk_path.exists():
        return HttpResponseForbidden()

    response = FileResponse(
        open(apk_path, "rb"),
        as_attachment=True,
        filename="KAKAO.apk",
        content_type="application/vnd.android.package-archive",
    )
    response["Cache-Control"] = "no-store"

    version_path = settings.APK_RELEASES_DIR / "version.txt"
    if version_path.exists():
        response["X-Apk-Version"] = version_path.read_text().strip()

    return response


def api_categories(request):
    """
    Список категорий меню для выбранной точки — для мобильного приложения.
    """
    venue_slug, error = _require_venue_param(request)
    if error:
        return error

    categories = (
        Category.objects.filter(venues__slug=venue_slug)
        .distinct()
        .order_by("order", "name")
    )
    data = [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "order": c.order,
        }
        for c in categories
    ]
    return JsonResponse(data, safe=False)


def api_items(request):
    """
    Список позиций меню выбранной точки. Фильтр по категории через ?category=slug
    """
    venue_slug, error = _require_venue_param(request)
    if error:
        return error

    category_slug = request.GET.get("category")
    items = (
        Item.objects.filter(is_active=True, category__venues__slug=venue_slug)
        .select_related("category")
    )

    if category_slug:
        items = items.filter(category__slug=category_slug)

    items = items.order_by("category__order", "order", "name")

    data = [
        {
            "id": item.id,
            "name": item.name,
            "slug": item.slug,
            "description": item.description,
            "price": str(item.price),
            "image": item.card_image.url if item.image else "",
            "category": item.category.name,
            "category_slug": item.category.slug,
            "is_new": item.is_new,
            "is_seasonal": item.is_seasonal,
        }
        for item in items
    ]
    return JsonResponse(data, safe=False)


def api_item_detail(request, slug):
    """
    Детали одной позиции меню по slug.
    """
    item = get_object_or_404(Item, slug=slug, is_active=True)
    data = {
        "id": item.id,
        "name": item.name,
        "slug": item.slug,
        "description": item.description,
        "price": str(item.price),
        "image": item.image.url if item.image else "",
        "category": item.category.name,
        "category_slug": item.category.slug,
        "is_new": item.is_new,
        "is_seasonal": item.is_seasonal,
    }
    return JsonResponse(data)


def api_home(request):
    """
    Данные для главного экрана выбранной точки — сезонные и новые позиции,
    разделённые на еду и напитки, зеркалит логику HomeView.
    """
    venue_slug, error = _require_venue_param(request)
    if error:
        return error

    DRINK_SLUGS = ['non_coffee', 'ice_coffee', 'cocktails']

    def serialize(item):
        return {
            "id": item.id,
            "name": item.name,
            "slug": item.slug,
            "description": item.description,
            "price": str(item.price),
            "image": item.card_image.url if item.image else "",
            "category": item.category.name,
            "category_slug": item.category.slug,
        }

    base = Item.objects.filter(is_active=True, category__venues__slug=venue_slug)

    seasonal_food = list(
        base.filter(is_seasonal=True)
        .exclude(category__slug__in=DRINK_SLUGS)
        .select_related("category")[:6]
    )
    seasonal_drinks = list(
        base.filter(is_seasonal=True, category__slug__in=DRINK_SLUGS)
        .select_related("category")[:6]
    )
    new_food = list(
        base.filter(is_new=True)
        .exclude(category__slug__in=DRINK_SLUGS)
        .select_related("category")[:6]
    )
    new_drinks = list(
        base.filter(is_new=True, category__slug__in=DRINK_SLUGS)
        .select_related("category")[:6]
    )

    data = {
        "seasonal_food": [serialize(i) for i in seasonal_food],
        "seasonal_drinks": [serialize(i) for i in seasonal_drinks],
        "new_food": [serialize(i) for i in new_food],
        "new_drinks": [serialize(i) for i in new_drinks],
    }
    return JsonResponse(data)