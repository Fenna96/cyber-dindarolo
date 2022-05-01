from django.db import models
from django.contrib.auth.models import User

"""
Limita il credito a +- il valore indicato per ogni utente
"""
BALANCE_LIMIT = 500

# Create your models here.
class Balance(models.Model):
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.CASCADE
    )  # each id correspond to a user in User table
    balance = models.DecimalField(
        max_digits=256, decimal_places=2
    )  # decimal with 2 max decimals

    def stars(self):
        return (self.balance + 500) / 200

    user_stars = property(stars)

    def __str__(self):
        return f'"{self.user.username}" balance: {self.balance}'


class Category(models.Model):
    name = models.CharField(max_length=20, primary_key=True)

    def __str__(self):
        return f"{self.name}"


class Product(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    category = models.ForeignKey(Category, to_field="name", on_delete=models.CASCADE)

    def __str__(self):
        return f'Product "{self.name}" of category "{self.category}" '


class Transaction(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # each id correspond to a user in User table (can have multiple transaction for one user)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE
    )  # at each transaction is assigned exactly one product (can have multiple transactions assigned to the same product)
    date = models.DateTimeField(
        auto_now_add=True, blank=True
    )  # add date to track transactions in a specified interval
    amount = models.DecimalField(
        max_digits=256, decimal_places=2
    )  # add amount to track transactions, per analisi

    def __str__(self):
        return f'{self.date.strftime("%a, %d %b")} | {self.user.username}: {self.product}. {self.amount}'


class CatalogItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # each id correspond to a user in User table (can have multiple transaction for one user)
    product = models.ForeignKey(
        Product, to_field="name", on_delete=models.CASCADE
    )  # at each transaction is assigned exactly one product (can have multiple transactions assigned to the same product)
    quantity = models.IntegerField(
        default=1
    )  # you can assigne multiple products, one by deafult
    date = models.DateTimeField(
        auto_now_add=True, blank=True
    )  # add date to track transactions in a specified interval
    price = models.DecimalField(
        max_digits=256, decimal_places=2
    )  # add prize to track transactions, per analisi

    def __str__(self):
        return f' "{self.product.name}" | {self.date.strftime("%a, %d %b")} {self.user.username}: {self.quantity} , {self.price}'


class Product_pricetracker(models.Model):
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # id of the user who sold that product
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE
    )  # at each transaction is assigned exactly one product (can have multiple transactions assigned to the same product)
    date = models.DateTimeField(
        auto_now_add=True, blank=True
    )  # add date to track transactions in a specified interval
    price = models.DecimalField(
        max_digits=256, decimal_places=2
    )  # add prize to track transactions, per analisi

    def __str__(self):
        return (
            f' "{self.product.name}" | {self.date.strftime("%a, %d %b")}: {self.price}'
        )
