from django.test import SimpleTestCase
from django.urls import reverse,resolve
from manager.views import index
class TestUrls(SimpleTestCase):

    def test_index_url(self):
        self.assertEquals(resolve(reverse('manager:index')).func, index)