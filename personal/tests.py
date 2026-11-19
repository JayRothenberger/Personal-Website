from django.test import SimpleTestCase, override_settings
from django.urls import reverse

# Tests run without collectstatic, so use the plain storage instead of the
# manifest storage used in production.
PLAIN_STATIC = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

PAGES = ["index", "ponder", "blog", "cv", "resume", "links", "planetarium"]


@override_settings(STORAGES=PLAIN_STATIC, SECURE_SSL_REDIRECT=False)
class PageTests(SimpleTestCase):
    def test_pages_render(self):
        for name in PAGES:
            with self.subTest(page=name):
                response = self.client.get(reverse(f"personal:{name}"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "<!DOCTYPE html>")

    def test_pages_reject_post(self):
        response = self.client.post(reverse("personal:index"), {"torun": "1"})
        self.assertEqual(response.status_code, 405)

    def test_code_execution_endpoints_are_gone(self):
        for path in ["/run/?torun=1", "/rendezvous/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
