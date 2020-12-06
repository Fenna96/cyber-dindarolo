import pprint

from django.test import TestCase, Client
from django.urls import reverse
from manager.models import Category, Product, Product_pricetracker, Balance, BALANCE_LIMIT, Catalog, User, Transaction

class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        #Fake user setup
        self.username = 'Martina'
        self.password = 'marti'
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()
        #setting up his balance to 200
        balance = Balance.objects.create(user=user,balance=200)
        self.redirect_url = '/?next='
        self.index_url = reverse("market:index")
        self.insert_url = reverse('market:insert')
        self.catalog_url = reverse('market:catalog')
        self.user_items_url = reverse('market:user_items')
        self.add_item_url = reverse('market:add_item')
        self.buy_item_url = reverse('market:buy_item')
        self.remove_item_url = reverse('market:remove_item')

    def test_index_methods(self):
        #Testing redirection
        get_response = self.client.get(self.index_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username,password=self.password)
        get_response = self.client.get(self.index_url)
        post_response = self.client.post(self.index_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_insert_methods(self):
        #Testing redirection
        get_response = self.client.get(self.insert_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username,password=self.password)
        get_response = self.client.get(self.insert_url)
        post_response = self.client.post(self.insert_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_catalog_methods(self):
        # Testing redirection
        get_response = self.client.get(self.catalog_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.catalog_url)
        post_response = self.client.post(self.catalog_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_catalog_not_your_products(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta', category=cat)
        prod.save()

        user = User.objects.get(username=self.username)

        item = Catalog.objects.create(user=user, product=prod, quantity=3, price=2)
        item.save()

        get_response = self.client.get(self.catalog_url)

        self.assertEquals(get_response.context['groups'], [])
        self.client.logout()

    def test_user_items_methods(self):
        # Testing redirection
        get_response = self.client.get(self.user_items_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.user_items_url)
        post_response = self.client.post(self.user_items_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_user_items_your_products(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta', category=cat)
        prod.save()

        user = User.objects.get(username=self.username)

        item = Catalog.objects.create(user=user, product=prod, quantity=3, price=2)
        item.save()

        get_response = self.client.get(self.user_items_url)

        self.assertEquals(get_response.context['catalog'][0], item)
        self.client.logout()

    def test_add_item_methods(self):
        # Testing redirection
        get_response = self.client.get(self.add_item_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.add_item_url)
        post_response = self.client.post(self.add_item_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)   #post with no arguments

        self.client.logout()

    def test_add_item_paths(self):
        #Testing redirection
        get_response = self.client.get(self.add_item_url)
        self.assertEquals(get_response.url, self.redirect_url+self.add_item_url)

        self.client.login(username=self.username, password=self.password)

        #Testing what is printed when bad request
        post_response = self.client.post(self.add_item_url)
        self.assertTemplateUsed(post_response, 'market/insert.html')  # post with no arguments

        #Testint what happens when method not allower
        get_response = self.client.get(self.add_item_url)
        self.assertEquals(get_response.url, self.insert_url)

    def test_add_item_validated_post(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        post_response = self.client.post(self.add_item_url, {
            'product-name':'Pasta',
            'product-category':'Food',
            'catalog-price':1,
            'catalog-quantity':2
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_add_item_category_not_found(self):
        self.client.login(username=self.username, password=self.password)

        post_response = self.client.post(self.add_item_url, {
            'product-name':'Pasta',
            'product-category':'Food',
            'catalog-price':1,
            'catalog-quantity':2
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_add_item_price_over_limit(self):
        self.client.login(username=self.username, password=self.password)

        response = self.client.post(self.add_item_url, {
            'product-name':'Pasta',
            'product-category':'Food',
            'catalog-price':BALANCE_LIMIT+1,
            'catalog-quantity':2
        })

        self.assertFormError(response, 'catalog_form', 'price', "You can't sell at more than price limit!")
        self.client.logout()

    def test_add_item_product_name_required(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        response = self.client.post(self.add_item_url, {
            'product-category': 'Food',
            'catalog-price': 2,
            'catalog-quantity': 2
        })

        self.assertFormError(response, 'product_form', 'name', "This field is required.")
        self.client.logout()

    def test_add_item_product_category_required(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        response = self.client.post(self.add_item_url, {
            'product-name': 'Pasta',
            'catalog-price': 2,
            'catalog-quantity': 2
        })

        self.assertFormError(response, 'product_form', 'category', "This field is required.")
        self.client.logout()

    def test_add_item_product_price_required(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        response = self.client.post(self.add_item_url, {
            'product-name': 'Pasta',
            'product-category': 'Food',
            'catalog-quantity': 2
        })

        self.assertFormError(response, 'catalog_form', 'price', "This field is required.")
        self.client.logout()

    def test_add_item_product_quantity_required(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        response = self.client.post(self.add_item_url, {
            'product-name': 'Pasta',
            'product-category': 'Food',
            'catalog-price': 2
        })

        self.assertFormError(response, 'catalog_form', 'quantity', "This field is required.")
        self.client.logout()

    def test_buy_item_methods(self):
        # Testing redirection
        get_response = self.client.get(self.buy_item_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.buy_item_url)
        post_response = self.client.post(self.buy_item_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)   #post with no arguments

        self.client.logout()

    def test_buy_item_paths(self):
        #Testing redirection
        get_response = self.client.get(self.buy_item_url)
        self.assertEquals(get_response.url, self.redirect_url+self.buy_item_url)

        self.client.login(username=self.username, password=self.password)

        #Testing what is printed when bad request
        post_response = self.client.post(self.buy_item_url)
        self.assertEquals(post_response.url, self.catalog_url + '/Something%20wrong%20with%20your%20request.')  # post with no arguments

        #Testint what happens when method not allowed
        get_response = self.client.get(self.buy_item_url)
        self.assertEquals(get_response.url, self.catalog_url)

    def test_buy_item_validated_post(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':2
        })

        self.assertEquals(post_response.status_code,200)
        self.client.logout()

    def test_buy_item_no_id(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.buy_item_url, {
            'quantity':2
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_buy_item_no_quantity(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1'
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_buy_item_not_found_in_catalog(self):
        self.client.login(username=self.username, password=self.password)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':2
        })

        self.assertEquals(post_response.status_code,302)
        self.assertEquals(post_response.url,self.catalog_url+"/Couldn't%20find%20the%20item%20requested%20in%20catalog.")
        self.client.logout()

    def test_buy_item_quantity_over_limit(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':4
        })

        self.assertEquals(post_response.status_code,302)
        self.assertEquals(post_response.url,self.catalog_url + "/You%20tried%20to%20buy,%20but%20we%20don't%20have%20that%20much!")
        self.client.logout()

    def test_buy_item_price_over_limit(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=201+BALANCE_LIMIT)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':1
        })

        self.assertEquals(post_response.status_code,302)
        self.assertEquals(post_response.url,self.catalog_url + "/You%20don't%20have%20enough%20credits%20(limit%20reached).")
        self.client.logout()

    def test_buy_item_product_not_found(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        prod.delete()

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':2
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_buy_item_user_not_found(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        user = User.objects.create(username='Fenna96')
        user.set_password('pisellone96')
        user.save()

        item = Catalog.objects.create(user=user, product=prod, quantity=3, price=2)

        user.delete()

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':2
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_buy_item_seller_balance_over(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        user = User.objects.create(username='Fenna96')
        user.save()

        balance = Balance.objects.create(user=user,balance=499)
        balance.save()

        item = Catalog.objects.create(user=user, product=prod, quantity=3, price=200)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':2
        })

        self.assertEquals(post_response.status_code,200)
        self.assertEquals(Balance.objects.get(user=user).balance,500)
        self.client.logout()

    def test_buy_item_not_removed_item(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':2
        })

        self.assertEquals(post_response.status_code,200)
        self.assertTrue(Catalog.objects.get(id=item.id).quantity==1)
        self.client.logout()

    def test_buy_item_removed_item(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta', category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.buy_item_url, {
            'item_id': '1',
            'quantity': 3
        })

        self.assertEquals(post_response.status_code, 200)
        self.assertFalse(Catalog.objects.filter(id=item.id))
        self.client.logout()

    def test_buy_item_tracks_created(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()


        user = User.objects.create(username='Fenna96')
        user.save()

        balance = Balance.objects.create(user=user, balance=200)
        balance.save()


        item = Catalog.objects.create(user=user, product=prod, quantity=3, price=2)

        post_response = self.client.post(self.buy_item_url, {
            'item_id':'1',
            'quantity':2
        })

        self.assertEquals(post_response.status_code,200)
        self.assertTrue(Transaction.objects.all())
        self.assertTrue(Product_pricetracker.objects.filter(seller=user, product=prod, price=2))
        self.client.logout()

    def test_remove_item_methods(self):
        # Testing redirection
        get_response = self.client.get(self.remove_item_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.remove_item_url)
        post_response = self.client.post(self.remove_item_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)   #post with no arguments

        self.client.logout()

    def test_remove_item_paths(self):
        # Testing redirection
        get_response = self.client.get(self.remove_item_url)
        self.assertEquals(get_response.url, self.redirect_url + self.remove_item_url)

        self.client.login(username=self.username, password=self.password)

        # Testing what is printed when bad request
        post_response = self.client.post(self.remove_item_url)
        self.assertEquals(post_response.url,
                          self.user_items_url + '/Something%20wrong%20with%20your%20request.')  # post with no arguments

        # Testint what happens when method not allowed
        get_response = self.client.get(self.remove_item_url)
        self.assertEquals(get_response.url, self.user_items_url)

    def test_remove_item_validated_post(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.remove_item_url, {
            'item_id':1
        })

        self.assertEquals(post_response.status_code,302)
        self.assertFalse(Catalog.objects.filter(id=item.id))
        self.client.logout()

    def test_remove_item_not_found(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.remove_item_url, {
            'item_id':2
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_remove_item_no_id(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        post_response = self.client.post(self.remove_item_url, {
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()

    def test_remove_item_no_product(self):
        self.client.login(username=self.username, password=self.password)

        cat = Category.objects.create(name='Food')
        cat.save()

        prod = Product.objects.create(name='Pasta',category=cat)
        prod.save()

        item = Catalog.objects.create(user=User.objects.get(username=self.username), product=prod, quantity=3, price=2)

        prod.delete()

        post_response = self.client.post(self.remove_item_url, {
            'item_id':1
        })

        self.assertEquals(post_response.status_code,302)
        self.client.logout()


