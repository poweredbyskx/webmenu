import time

from django.test import TestCase

from menu.models import Category, Venue


def make_venue(**kwargs):
    kwargs.setdefault("name", "Тестовое заведение")
    kwargs.setdefault("slug", "test-venue")
    venue, _ = Venue.objects.get_or_create(slug=kwargs["slug"], defaults=kwargs)
    return venue


def make_category(**kwargs):
    venues = kwargs.pop("venues", None)
    if venues is None:
        venues = [make_venue()]
    category = Category.objects.create(**kwargs)
    category.venues.set(venues)
    return category


class VenueSessionTestCase(TestCase):
    """
    Базовый TestCase для вьюх сайта: кладёт venue_slug в сессию клиента,
    чтобы VenueSelectionMiddleware не редиректил запросы на select_venue.
    Наследники, переопределяющие setUp, должны звать super().setUp().
    """

    def setUp(self):
        super().setUp()
        self.venue = make_venue()
        session = self.client.session
        session["venue_slug"] = self.venue.slug
        session["venue_set_at"] = time.time()
        session.save()
