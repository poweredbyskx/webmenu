from django.test import TestCase
from django.urls import reverse

from menu.models import Category, Item, RoastedCoffee


class HomeViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Тестовая категория", slug="test-category", order=0)
        self.active_item = Item.objects.create(
            category=self.category, name="Латте", price=50, is_active=True,
            is_new=True, is_seasonal=True,
        )
        self.inactive_item = Item.objects.create(
            category=self.category, name="Архивный латте", price=50, is_active=False,
            is_new=True, is_seasonal=True,
        )

    def test_status_code(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_inactive_items_excluded_from_new_and_seasonal(self):
        response = self.client.get(reverse("home"))
        self.assertNotIn(self.inactive_item, response.context["new_food"])
        self.assertNotIn(self.inactive_item, response.context["seasonal_food"])
        self.assertIn(self.active_item, response.context["new_food"])
        self.assertIn(self.active_item, response.context["seasonal_food"])

    def test_menu_items_only_active_from_first_category(self):
        response = self.client.get(reverse("home"))
        self.assertIn(self.active_item, response.context["menu_items"])
        self.assertNotIn(self.inactive_item, response.context["menu_items"])

    def test_no_categories_does_not_error(self):
        Category.objects.all().delete()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)


class MenuViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Тестовая категория", slug="test-category")
        self.active_item = Item.objects.create(
            category=self.category, name="Латте", price=50, is_active=True,
        )
        self.inactive_item = Item.objects.create(
            category=self.category, name="Архивный латте", price=50, is_active=False,
        )

    def test_status_code(self):
        response = self.client.get(reverse("menu"))
        self.assertEqual(response.status_code, 200)

    def test_only_active_items_listed(self):
        response = self.client.get(reverse("menu"))
        items = list(response.context["items"])
        self.assertIn(self.active_item, items)
        self.assertNotIn(self.inactive_item, items)


class CategoryViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Кофе", slug="coffee")
        self.active_item = Item.objects.create(
            category=self.category, name="Латте", price=50, is_active=True,
        )
        self.inactive_item = Item.objects.create(
            category=self.category, name="Архивный латте", price=50, is_active=False,
        )

    def test_status_code(self):
        response = self.client.get(reverse("category", args=["coffee"]))
        self.assertEqual(response.status_code, 200)

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse("category", args=["does-not-exist"]))
        self.assertEqual(response.status_code, 404)

    def test_only_active_items_in_this_category(self):
        other_category = Category.objects.create(name="Чай", slug="tea")
        other_item = Item.objects.create(
            category=other_category, name="Чай зелёный", price=30, is_active=True,
        )
        response = self.client.get(reverse("category", args=["coffee"]))
        items = list(response.context["items"])
        self.assertIn(self.active_item, items)
        self.assertNotIn(self.inactive_item, items)
        self.assertNotIn(other_item, items)


class RoastedViewTests(TestCase):
    def test_status_code(self):
        response = self.client.get(reverse("roasted"))
        self.assertEqual(response.status_code, 200)

    def test_only_active_coffees_listed(self):
        active = RoastedCoffee.objects.create(name="Эфиопия", price=300, is_active=True)
        inactive = RoastedCoffee.objects.create(name="Кения", price=300, is_active=False)
        response = self.client.get(reverse("roasted"))
        coffees = list(response.context["coffees"])
        self.assertIn(active, coffees)
        self.assertNotIn(inactive, coffees)


class BeansViewTests(TestCase):
    def test_status_code(self):
        response = self.client.get(reverse("beans"))
        self.assertEqual(response.status_code, 200)
