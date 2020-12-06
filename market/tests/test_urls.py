from django.test import SimpleTestCase
from django.urls import reverse,resolve
from market.views import index, insert, catalog, user_items, remove_item, add_item, buy_item
class TestUrls(SimpleTestCase):

    def test_index_url(self):
        self.assertEquals(resolve(reverse('market:index')).func, index)
    def test_insert_url(self):
        self.assertEquals(resolve(reverse('market:insert')).func, insert)
    def test_catalog_url(self):
        self.assertEquals(resolve(reverse('market:catalog')).func, catalog)
    def test_user_items_url(self):
        self.assertEquals(resolve(reverse('market:user_items')).func, user_items)
    def test_add_item_url(self):
        self.assertEquals(resolve(reverse('market:add_item')).func, add_item)
    def test_buy_item_url(self):
        self.assertEquals(resolve(reverse('market:buy_item')).func, buy_item)
    def test_remove_item_url(self):
        self.assertEquals(resolve(reverse('market:remove_item')).func, remove_item)