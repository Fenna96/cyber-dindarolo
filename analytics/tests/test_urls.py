from django.test import SimpleTestCase
from django.urls import reverse,resolve
from analytics.views import history, index, price_tracker, search_page, search_product
class TestUrls(SimpleTestCase):

    def test_index_url(self):
        self.assertEquals(resolve(reverse('analytics:index')).func, index)
    def test_history_url(self):
        self.assertEquals(resolve(reverse('analytics:history')).func, history)
    def test_price_tracker_url(self):
        self.assertEquals(resolve(reverse('analytics:price_tracker',  kwargs={'item':'Pasta'})).func, price_tracker)
    def test_search_page_url(self):
        self.assertEquals(resolve(reverse('analytics:search')).func, search_page)
    def test_search_product_url(self):
        self.assertEquals(resolve(reverse('analytics:search_product')).func, search_product)
