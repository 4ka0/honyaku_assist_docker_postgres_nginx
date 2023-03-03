from django.urls import reverse
from django.test import SimpleTestCase


class TestInputPage(SimpleTestCase):

    def test_input_page_exists_at_desired_url(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)

    def test_input_page_accessible_by_name(self):
        response = self.client.get(reverse('input'))
        self.assertEqual(response.status_code, 200)

    def test_input_page_uses_correct_template(self):
        response = self.client.get(reverse('input'))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'input.html')

    def test_input_page_title_and_navbar_content(self):
        response = self.client.get(reverse('input'))
        self.assertContains(response, '<title>Honyaku Assist</title>')

    def test_input_page_navbar_content(self):
        response = self.client.get(reverse('input'))
        self.assertContains(response, '<a class="navbar-brand" href="/">Honyaku Assist</a>')
        self.assertContains(response, '<span class="navbar-text">A machine translation assistant for')

    def test_input_page_form_content(self):
        response = self.client.get(reverse('input'))
        self.assertContains(response, 'Japanese to English')
        self.assertContains(response, 'English to Japanese')
        self.assertContains(response, 'Translate</button>')