from django.test import TestCase
from django.urls import reverse

from menu.tests.factories import make_venue


class VenueSelectionMiddlewareTests(TestCase):
    def test_redirects_to_select_venue_when_no_venue_in_session(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("select_venue"), response.url)

    def test_passes_through_when_venue_in_session(self):
        # /menu/, не "/" — главная сейчас намеренно всегда переспрашивает
        # точку заново (см. test_home_page_always_reasks_unless_just_set),
        # это отдельное поведение только для неё.
        venue = make_venue()
        session = self.client.session
        session["venue_slug"] = venue.slug
        session.save()

        response = self.client.get(reverse("menu"))
        self.assertEqual(response.status_code, 200)

    def test_resets_session_and_redirects_when_venue_deactivated(self):
        venue = make_venue(slug="inactive-venue", is_active=False)
        session = self.client.session
        session["venue_slug"] = venue.slug
        session.save()

        response = self.client.get(reverse("menu"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("select_venue"), response.url)
        self.assertNotIn("venue_slug", self.client.session)

    def test_home_page_always_reasks_unless_just_set(self):
        # Временное поведение для удобства ручного тестирования: "/" всегда
        # переспрашивает точку при обновлении, кроме самого первого захода
        # сразу после set_venue (иначе — бесконечный редирект).
        venue = make_venue()
        session = self.client.session
        session["venue_slug"] = venue.slug
        session.save()

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("select_venue"), response.url)

    def test_home_page_passes_through_right_after_set_venue(self):
        venue = make_venue()
        response = self.client.get(
            reverse("set_venue", args=[venue.slug]), {"next": reverse("home")}
        )
        self.assertRedirects(response, reverse("home"))

    def test_api_paths_are_exempt_even_without_venue(self):
        response = self.client.get(reverse("api_categories"))
        # 400 (missing ?venue=), not a 302 redirect to select_venue —
        # confirms /api/ is not blocked by the session-based check.
        self.assertEqual(response.status_code, 400)

    def test_select_venue_page_itself_is_exempt(self):
        response = self.client.get(reverse("select_venue"))
        self.assertEqual(response.status_code, 200)
