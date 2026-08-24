import json

from django.test import TestCase
from django.urls import reverse

from menu.models import Item
from menu.tests.factories import make_category, make_venue


class ApiVenueIsolationTests(TestCase):
    def setUp(self):
        self.venue_a = make_venue(name="Точка A", slug="venue-a")
        self.venue_b = make_venue(name="Точка B", slug="venue-b")

        self.category_a = make_category(name="Только A", venues=[self.venue_a])
        self.category_b = make_category(name="Только B", venues=[self.venue_b])
        self.category_shared = make_category(
            name="Общая", venues=[self.venue_a, self.venue_b]
        )

        self.item_a = Item.objects.create(
            category=self.category_a, name="Товар A", price=10, is_active=True,
        )
        self.item_b = Item.objects.create(
            category=self.category_b, name="Товар B", price=10, is_active=True,
        )
        self.item_shared = Item.objects.create(
            category=self.category_shared, name="Товар общий", price=10, is_active=True,
        )

    # --- api_categories -----------------------------------------------

    def test_api_categories_requires_venue_param(self):
        response = self.client.get(reverse("api_categories"))
        self.assertEqual(response.status_code, 400)

    def test_api_categories_scoped_to_venue(self):
        response = self.client.get(reverse("api_categories"), {"venue": "venue-a"})
        slugs = [c["slug"] for c in json.loads(response.content)]
        self.assertIn(self.category_a.slug, slugs)
        self.assertIn(self.category_shared.slug, slugs)
        self.assertNotIn(self.category_b.slug, slugs)

    def test_api_categories_no_duplicates_for_shared_category(self):
        response = self.client.get(reverse("api_categories"), {"venue": "venue-a"})
        slugs = [c["slug"] for c in json.loads(response.content)]
        self.assertEqual(slugs.count(self.category_shared.slug), 1)

    # --- api_items -------------------------------------------------------

    def test_api_items_requires_venue_param(self):
        response = self.client.get(reverse("api_items"))
        self.assertEqual(response.status_code, 400)

    def test_api_items_scoped_to_venue(self):
        response = self.client.get(reverse("api_items"), {"venue": "venue-a"})
        names = [i["name"] for i in json.loads(response.content)]
        self.assertIn(self.item_a.name, names)
        self.assertIn(self.item_shared.name, names)
        self.assertNotIn(self.item_b.name, names)

    def test_api_items_combines_with_category_filter(self):
        response = self.client.get(
            reverse("api_items"), {"venue": "venue-a", "category": self.category_a.slug}
        )
        names = [i["name"] for i in json.loads(response.content)]
        self.assertEqual(names, [self.item_a.name])

    # --- api_home ----------------------------------------------------------

    def test_api_home_requires_venue_param(self):
        response = self.client.get(reverse("api_home"))
        self.assertEqual(response.status_code, 400)

    def test_api_home_excludes_other_venue_items(self):
        self.item_a.is_new = True
        self.item_a.save()
        self.item_b.is_new = True
        self.item_b.save()

        response = self.client.get(reverse("api_home"), {"venue": "venue-a"})
        data = json.loads(response.content)
        all_names = [i["name"] for group in data.values() for i in group]
        self.assertIn(self.item_a.name, all_names)
        self.assertNotIn(self.item_b.name, all_names)
