import time

from django.test import TestCase
from django.urls import reverse

from menu.middleware import VENUE_SESSION_TTL_SECONDS
from menu.tests.factories import make_venue


class VenueSelectionMiddlewareTests(TestCase):
    def test_redirects_to_select_venue_when_no_venue_in_session(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("select_venue"), response.url)

    def test_passes_through_when_venue_freshly_chosen(self):
        venue = make_venue()
        session = self.client.session
        session["venue_slug"] = venue.slug
        session["venue_set_at"] = time.time()
        session.save()

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_redirects_when_venue_choice_older_than_a_day(self):
        # Выбор точки живёт сутки — по истечении срока сайт должен снова
        # спросить, какое кафе показывать, а не молча держаться за старое.
        venue = make_venue()
        session = self.client.session
        session["venue_slug"] = venue.slug
        session["venue_set_at"] = time.time() - VENUE_SESSION_TTL_SECONDS - 1
        session.save()

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("select_venue"), response.url)
        self.assertNotIn("venue_slug", self.client.session)

    def test_resets_session_and_redirects_when_venue_deactivated(self):
        venue = make_venue(slug="inactive-venue", is_active=False)
        session = self.client.session
        session["venue_slug"] = venue.slug
        session["venue_set_at"] = time.time()
        session.save()

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("select_venue"), response.url)
        self.assertNotIn("venue_slug", self.client.session)

    def test_api_paths_are_exempt_even_without_venue(self):
        response = self.client.get(reverse("api_categories"))
        # 400 (missing ?venue=), not a 302 redirect to select_venue —
        # confirms /api/ is not blocked by the session-based check.
        self.assertEqual(response.status_code, 400)

    def test_select_venue_page_itself_is_exempt(self):
        response = self.client.get(reverse("select_venue"))
        self.assertEqual(response.status_code, 200)
