from django.contrib import admin

# Register your models here.
from .models import Balance, Category, Product, Catalog, Transaction, Product_pricetracker

admin.site.register(Balance)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Transaction)
admin.site.register(Catalog)
admin.site.register(Product_pricetracker)
