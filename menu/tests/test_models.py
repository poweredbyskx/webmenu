from django.db import IntegrityError, transaction
from django.test import TestCase

from menu.models import Category, Item, RoastedCoffee


class CategorySlugTests(TestCase):
    def test_slug_is_generated_from_name(self):
        category = Category.objects.create(name="Тестовая новинка")
        self.assertEqual(category.slug, "testovaia-novinka")

    def test_explicit_slug_is_not_overwritten(self):
        category = Category.objects.create(name="Кофе", slug="custom-slug")
        self.assertEqual(category.slug, "custom-slug")

    def test_duplicate_slug_raises_integrity_error(self):
        Category.objects.create(name="Кофе", slug="coffee")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="Кофе 2", slug="coffee")

    def test_ordering_by_order_then_name(self):
        # 0002_seed_categories подсевает свои категории в тестовую БД —
        # начинаем с чистого листа, чтобы проверять только сортировку.
        Category.objects.all().delete()
        c_b = Category.objects.create(name="Б категория", order=1)
        c_a = Category.objects.create(name="А категория", order=1)
        c_first = Category.objects.create(name="Всегда первая", order=0)
        self.assertEqual(
            list(Category.objects.all()), [c_first, c_a, c_b]
        )

    def test_str_returns_name(self):
        category = Category.objects.create(name="Завтраки")
        self.assertEqual(str(category), "Завтраки")


class ItemModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Тестовая категория", slug="test-category")

    def test_slug_is_generated_from_name(self):
        item = Item.objects.create(category=self.category, name="Латте", price=50)
        self.assertEqual(item.slug, "latte")

    def test_negative_price_is_rejected_by_validator(self):
        item = Item(category=self.category, name="Латте", price=-10)
        with self.assertRaises(Exception):
            item.full_clean()

    def test_ordering_by_order_then_name(self):
        i_b = Item.objects.create(category=self.category, name="Б", price=1, order=1)
        i_a = Item.objects.create(category=self.category, name="А", price=1, order=1)
        i_first = Item.objects.create(category=self.category, name="Первый", price=1, order=0)
        self.assertEqual(list(Item.objects.all()), [i_first, i_a, i_b])

    def test_category_deletion_cascades_to_items(self):
        item = Item.objects.create(category=self.category, name="Латте", price=50)
        self.category.delete()
        self.assertFalse(Item.objects.filter(pk=item.pk).exists())


class RoastedCoffeeModelTests(TestCase):
    def test_slug_is_generated_from_name(self):
        coffee = RoastedCoffee.objects.create(name="Эфиопия Сидамо", price=300)
        self.assertEqual(coffee.slug, "efiopiia-sidamo")

    def test_str_returns_name(self):
        coffee = RoastedCoffee.objects.create(name="Бразилия Сантос", price=250)
        self.assertEqual(str(coffee), "Бразилия Сантос")
