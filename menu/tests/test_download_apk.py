import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class DownloadApkTests(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.releases_dir = Path(self.tmp_dir.name)
        self.addCleanup(self.tmp_dir.cleanup)

        self.staff_user = User.objects.create_user(
            "staff", password="pass", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            "regular", password="pass", is_staff=False
        )

    def _write_apk(self):
        (self.releases_dir / "KAKAO.apk").write_bytes(b"fake-apk-bytes")

    def test_anonymous_gets_403(self):
        with override_settings(APK_RELEASES_DIR=self.releases_dir):
            self._write_apk()
            response = self.client.get(reverse("download_apk"))
        self.assertEqual(response.status_code, 403)

    def test_regular_user_gets_403(self):
        self.client.force_login(self.regular_user)
        with override_settings(APK_RELEASES_DIR=self.releases_dir):
            self._write_apk()
            response = self.client.get(reverse("download_apk"))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_gets_403_when_file_missing(self):
        # Файл ещё не залит на сервер — не должно быть 500 или утечки,
        # что endpoint вообще существует.
        self.client.force_login(self.staff_user)
        with override_settings(APK_RELEASES_DIR=self.releases_dir):
            response = self.client.get(reverse("download_apk"))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_downloads_apk_with_correct_headers(self):
        self.client.force_login(self.staff_user)
        with override_settings(APK_RELEASES_DIR=self.releases_dir):
            self._write_apk()
            response = self.client.get(reverse("download_apk"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], "application/vnd.android.package-archive"
        )
        self.assertIn('filename="KAKAO.apk"', response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(b"".join(response.streaming_content), b"fake-apk-bytes")

    def test_version_header_present_when_version_file_exists(self):
        self.client.force_login(self.staff_user)
        with override_settings(APK_RELEASES_DIR=self.releases_dir):
            self._write_apk()
            (self.releases_dir / "version.txt").write_text("1.4.2\n")
            response = self.client.get(reverse("download_apk"))

        self.assertEqual(response["X-Apk-Version"], "1.4.2")

    def test_download_apk_path_is_exempt_from_venue_middleware(self):
        # Без venue в сессии обычная страница редиректит на выбор точки —
        # этот путь не должен, иначе staff не сможет скачать apk без
        # выбранной точки.
        self.client.force_login(self.staff_user)
        with override_settings(APK_RELEASES_DIR=self.releases_dir):
            self._write_apk()
            response = self.client.get(reverse("download_apk"))
        self.assertEqual(response.status_code, 200)
