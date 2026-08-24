from django.test import TestCase
from django.urls import reverse

from menu.middleware import DEFAULT_VENUE_SLUG
from menu.models import Venue
from menu.tests.factories import make_venue


class VenueSelectionMiddlewareTests(TestCase):
    def test_defaults_to_default_venue_when_no_venue_in_session(self):
        # ВРЕМЕННО: пока kakao_gaudan наполняется контентом, свежий визит без
        # выбранной точки должен незаметно получить старое меню (Мир 4),
        # а не упираться в обязательный выбор.
        # Миграция 0012 уже создаёт kakao_mir4 сама — make_venue тут просто
        # идемпотентно подтверждает, что она существует.
        make_venue(slug=DEFAULT_VENUE_SLUG, name="Мир 4")

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["venue_slug"], DEFAULT_VENUE_SLUG)

    def test_redirects_to_select_venue_when_default_venue_missing(self):
        # Если дефолтная точка вообще не существует в базе — это не должно
        # тихо ломаться, а должно явно отправить на выбор. В реальности
        # миграция 0012 гарантирует, что kakao_mir4 существует — но
        # подстраховку на случай его удаления/деактивации всё равно стоит
        # проверять, поэтому явно убираем её здесь.
        Venue.objects.filter(slug=DEFAULT_VENUE_SLUG).delete()

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("select_venue"), response.url)

    def test_passes_through_when_venue_in_session(self):
        venue = make_venue()
        session = self.client.session
        session["venue_slug"] = venue.slug
        session.save()

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_resets_session_and_redirects_when_venue_deactivated(self):
        venue = make_venue(slug="inactive-venue", is_active=False)
        session = self.client.session
        session["venue_slug"] = venue.slug
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
