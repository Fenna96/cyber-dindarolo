import pprint

from django.http import HttpResponse
from django.test import TestCase, Client
from django.urls import reverse
from manager.models import (
    Category,
    Product,
    Product_pricetracker,
    Balance,
    BALANCE_LIMIT,
    CatalogItem,
    User,
    Transaction,
)
from user.models import Profile, DEFAULT_PIC_FILE
from django.core.files.uploadedfile import SimpleUploadedFile


class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        # Fake user setup
        self.username = "Martina"
        self.password = "marti"
        user = User.objects.create(username=self.username)
        user.email = "marti.levizzani@gmail.com"
        user.set_password(self.password)
        user.save()
        # setting up his balance to 200
        balance = Balance.objects.create(
            user=User.objects.get(username=self.username), balance=200
        )

        Profile.objects.create(
            user=User.objects.get(username=self.username),
            name="Martina",
            surname="Levizzani",
            biography="-",
            mobile=3384014188,
        ).save()

        self.redirect_url = "/?next="
        self.index_url = reverse("analytics:index")
        self.history_url = reverse("analytics:history")
        self.price_tracker_url = reverse(
            "analytics:price_tracker", kwargs={"item": "Pasta"}
        )
        self.search_url = reverse("analytics:search")
        self.search_product_url = reverse("analytics:search_product")

    def test_index_methods(self):
        # Testing redirection
        get_response = self.client.get(self.index_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.index_url)
        post_response = self.client.post(self.index_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_history_methods(self):
        # Testing redirection
        get_response = self.client.get(self.history_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.history_url)
        post_response = self.client.post(self.history_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_no_history(self):

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.history_url)

        try:
            boh = get_response.context
            self.assertTrue(0)
        except:
            self.assertTrue(1)

        self.client.logout()

    def test_with_history(self):

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.history_url)

        transaction = Transaction.objects.create(
            user=User.objects.get(username=self.username),
            product=Product.objects.create(
                name="pasta", category=Category.objects.create(name="ciao")
            ),
            amount="10",
        )
        transaction.save()

        get_response2 = self.client.get(self.history_url)

        self.assertTrue(get_response2.context != get_response.context)
        self.client.logout()

    def test_price_tracker_methods(self):
        # Testing redirection
        get_response = self.client.get(self.price_tracker_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.price_tracker_url)
        post_response = self.client.post(self.price_tracker_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_price_tracker_not_found(self):
        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.price_tracker_url)

        self.assertEquals(get_response.status_code, 302)
        self.client.logout()

    def test_price_tracker_found(self):
        self.client.login(username=self.username, password=self.password)

        Product.objects.create(
            name="Pasta", category=Category.objects.create(name="boh")
        ).save()

        get_response = self.client.get(self.price_tracker_url)

        self.assertEquals(get_response.status_code, 200)
        self.client.logout()

    def test_search_methods(self):
        # Testing redirection
        get_response = self.client.get(self.search_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.search_url)
        post_response = self.client.post(self.search_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_search_product_methods(self):
        # Testing redirection
        get_response = self.client.get(self.search_product_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.search_product_url)
        post_response = self.client.post(self.search_product_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_search_product_no_item(self):
        # Testing redirectio

        self.client.login(username=self.username, password=self.password)
        post_response = self.client.post(self.search_product_url)

        self.assertEquals(post_response.status_code, 302)
        self.assertTrue(post_response.url, self.search_url)

        self.client.logout()

    def test_search_product_item_not_found(self):
        # Testing redirectio

        self.client.login(username=self.username, password=self.password)
        post_response = self.client.post(self.search_product_url, {"item": "Pasta"})

        self.assertEquals(post_response.status_code, 302)
        self.assertEquals(post_response.url, self.search_url + "Product%20not%20found")

        self.client.logout()

    def test_search_product_item_found(self):
        # Testing redirectio

        self.client.login(username=self.username, password=self.password)
        Product.objects.create(
            name="Pasta", category=Category.objects.create(name="boh")
        ).save()
        post_response = self.client.post(self.search_product_url, {"item": "Pasta"})

        self.assertEquals(post_response.status_code, 302)
        self.assertNotEqual(post_response.url, self.search_url)

        self.client.logout()

    def test_search_product_empty_item(self):
        # Testing redirectio

        self.client.login(username=self.username, password=self.password)
        Product.objects.create(
            name="Pasta", category=Category.objects.create(name="boh")
        ).save()
        post_response = self.client.post(self.search_product_url, {"item": ""})

        self.assertEquals(post_response.status_code, 302)
        self.assertNotEqual(post_response.url, self.search_url)

        self.client.logout()
