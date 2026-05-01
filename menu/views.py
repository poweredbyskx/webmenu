import logging

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, TemplateView

from .models import Category, Item, RoastedCoffee


logger = logging.getLogger(__name__)

# Минимальная длина запроса — отсекает "а", "б" и пустые строки
MIN_QUERY_LEN = 2

# Поля, по которым ищем (все языки + категория)
SEARCH_FIELDS = [
    "name", "name_ru", "name_en", "name_tk",
    "description", "description_ru", "description_en", "description_tk",
    "category__name", "category__name_ru", "category__name_en", "category__name_tk",
]


def build_search_queryset(query: str):
    """
    Возвращает QuerySet items, отфильтрованный по подстроке в любом из языковых
    полей или в названии категории. Регистронезависимо (icontains = ILIKE в Postgres).
    """
    q = (query or "").strip()
    if len(q) < MIN_QUERY_LEN:
        return Item.objects.none()

    filters = Q()
    for field in SEARCH_FIELDS:
        filters |= Q(**{f"{field}__icontains": q})

    return (
        Item.objects
        .filter(filters)
        .select_related("category")
        .distinct()
        .order_by("category__order", "order", "name")
    )


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        categories = Category.objects.prefetch_related("items").all()
        first_category = categories.first()

        ctx["new_items"] = (
            Item.objects.filter(is_new=True, is_active=True).select_related("category")[:12]
        )
        ctx["seasonal_items"] = (
            Item.objects.filter(is_seasonal=True, is_active=True).select_related("category")[:12]
        )
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

        categories = Category.objects.all().order_by("order", "name")
        items = (
            Item.objects.filter(is_active=True)
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
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
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
        return build_search_queryset(self.q)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = getattr(self, "q", "")
        ctx["min_query_len"] = MIN_QUERY_LEN
        return ctx


def search_api(request):
    """
    JSON-эндпоинт для живого поиска с фронта.
    Возвращает максимум 10 результатов.
    """
    q = (request.GET.get("q") or "").strip()

    if len(q) < MIN_QUERY_LEN:
        return JsonResponse([], safe=False)

    qs = list(build_search_queryset(q)[:10])

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
        return ctx