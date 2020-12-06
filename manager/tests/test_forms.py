import pprint

from django.test import TestCase, Client
from django.urls import reverse
from manager.models import *
from manager.forms import *

class TestFroms(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='clothes')
        cat.save

    def test_product_form_valid(self):
        form = ProductForm(data={
            'name':'Pasta',
            'category':'clothes'
        })

        self.assertTrue(form.is_valid())

    def test_product_form_no_category(self):
        form = ProductForm(data={
            'name':'Pasta',
        })

        self.assertTrue(len(form.errors),1)

    def test_product_form_no_name(self):
        form = ProductForm(data={
            'category':'clothes'
        })

        self.assertTrue(len(form.errors),1)

    def test_product_form_category_not_found(self):
        form = ProductForm(data={
            'name':'Pasta',
            'category':'clothes2'
        })

        self.assertTrue(len(form.errors),1)

    def test_catalog_form_valid(self):
        Product.objects.create(name='Pasta',category=Category.objects.get(name='clothes')).save()
        form = InsertCatalogForm(data={
            'quantity':1,
            'price':1
        })

        self.assertTrue(form.is_valid())

    def test_catalog_form_no_quantity(self):
        Product.objects.create(name='Pasta', category=Category.objects.get(name='clothes')).save()
        form = InsertCatalogForm(data={
            'price': 1
        })

        self.assertEquals(len(form.errors),1)

    def test_catalog_form_no_price(self):
        Product.objects.create(name='Pasta', category=Category.objects.get(name='clothes')).save()
        form = InsertCatalogForm(data={
            'price': 1
        })

        self.assertEquals(len(form.errors),1)

    def test_catalog_form_price_over(self):
        Product.objects.create(name='Pasta',category=Category.objects.get(name='clothes')).save()
        form = InsertCatalogForm(data={
            'quantity':1,
            'price':BALANCE_LIMIT+1
        })

        self.assertEquals(len(form.errors),1)

    def test_catalog_form_quantity_integer(self):
        Product.objects.create(name='Pasta', category=Category.objects.get(name='clothes')).save()
        form = InsertCatalogForm(data={
            'quantity': 'ciao',
            'price': 1
        })

        self.assertEquals(len(form.errors), 1)

    def test_catalog_form_price_integer(self):
        Product.objects.create(name='Pasta', category=Category.objects.get(name='clothes')).save()
        form = InsertCatalogForm(data={
            'quantity': 1,
            'price': 'ciao'
        })

        self.assertEquals(len(form.errors), 1)




