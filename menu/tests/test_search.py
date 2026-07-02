import json

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, Item
from menu.views import MIN_QUERY_LEN, build_search_queryset


class BuildSearchQuerysetTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Тестовая категория", slug="test-category")
        self.latte = Item.objects.create(
            category=self.category, name="Латте", price=50, is_active=True,
        )

    def test_empty_query_returns_empty(self):
        self.assertEqual(list(build_search_queryset("")), [])

    def test_query_shorter_than_min_length_returns_empty(self):
        self.assertEqual(len("л"), 1)
        self.assertGreater(MIN_QUERY_LEN, 1)
        self.assertEqual(list(build_search_queryset("л")), [])

    def test_query_at_min_length_matches(self):
        query = self.latte.name[:MIN_QUERY_LEN]
        self.assertIn(self.latte, build_search_queryset(query))

    def test_matches_by_name_case_insensitive(self):
        # ASCII-запрос, чтобы тест был переносим между Postgres (прод/CI, ILIKE
        # умеет в регистронезависимость кириллицы) и SQLite (локальный smoke-run,
        # где LIKE регистронезависим только для ASCII).
        self.latte.name_en = "Latte"
        self.latte.save()
        self.assertIn(self.latte, build_search_queryset("LATTE"))

    def test_matches_by_translated_field(self):
        self.latte.name_en = "Latte"
        self.latte.save()
        self.assertIn(self.latte, build_search_queryset("Latte"))

    def test_matches_by_category_name(self):
        self.assertIn(self.latte, build_search_queryset("Тестовая категория"))

    def test_no_duplicate_rows_for_multi_field_match(self):
        # "Латте" встречается и в name, и потенциально совпадает по нескольким
        # OR-условиям сразу — distinct() должен схлопнуть это в одну строку.
        results = list(build_search_queryset("Латте"))
        self.assertEqual(results.count(self.latte), 1)

    def test_no_match_returns_empty(self):
        self.assertEqual(list(build_search_queryset("нет такого")), [])

    def test_inactive_items_are_excluded(self):
        inactive = Item.objects.create(
            category=self.category, name="Архивный латте", price=50, is_active=False,
        )
        self.assertNotIn(inactive, build_search_queryset("Архивный"))


class SearchViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Тестовая категория", slug="test-category")
        self.latte = Item.objects.create(
            category=self.category, name="Латте", price=50, is_active=True,
        )

    def test_status_code(self):
        response = self.client.get(reverse("search"), {"q": "Латте"})
        self.assertEqual(response.status_code, 200)

    def test_short_query_yields_no_results(self):
        response = self.client.get(reverse("search"), {"q": "л"})
        self.assertEqual(list(response.context["items"]), [])

    def test_missing_query_does_not_error(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)


class SearchApiTests(TestCase):
    def setUp(self):
        # django-ratelimit считает запросы через общий (process-wide) кэш —
        # чистим его, чтобы тесты не мешали друг другу и не ловили 403
        # из-за счётчика, накопленного в предыдущих тестах.
        cache.clear()
        self.category = Category.objects.create(name="Тестовая категория", slug="test-category")
        self.latte = Item.objects.create(
            category=self.category, name="Латте", price=50, is_active=True,
        )
        # Перечитываем из БД, чтобы price был Decimal с той же точностью
        # (decimal_places=2), что и в объекте, который отдаёт search_api.
        self.latte.refresh_from_db()

    def test_short_query_returns_empty_json_list(self):
        response = self.client.get(reverse("search_api"), {"q": "л"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test_returns_matching_item_shape(self):
        response = self.client.get(reverse("search_api"), {"q": "Латте"})
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        entry = data[0]
        self.assertEqual(entry["name"], self.latte.name)
        self.assertEqual(entry["price"], str(self.latte.price))
        self.assertEqual(entry["category_slug"], self.category.slug)
        self.assertEqual(entry["item_slug"], self.latte.slug)
        self.assertEqual(entry["image"], "")

    def test_results_are_capped_at_ten(self):
        for i in range(15):
            Item.objects.create(
                category=self.category, name=f"Латте {i}", price=50, is_active=True,
            )
        response = self.client.get(reverse("search_api"), {"q": "Латте"})
        data = json.loads(response.content)
        self.assertEqual(len(data), 10)


class SearchApiRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name="Тестовая категория", slug="test-category")
        Item.objects.create(category=self.category, name="Латте", price=50, is_active=True)

    def tearDown(self):
        cache.clear()

    def test_blocks_after_30_requests_per_minute(self):
        for _ in range(30):
            response = self.client.get(reverse("search_api"), {"q": "Латте"})
            self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("search_api"), {"q": "Латте"})
        self.assertEqual(response.status_code, 403)
