from django.contrib import admin
from django.urls import path,include
from . import views

app_name = 'market'
urlpatterns = [
    path('', views.index, name='index'),
    path('insert', views.insert, name='insert'),
    path('catalog/<str:error>', views.catalog, name='catalog'),
    path('catalog', views.catalog, name='catalog'),
    path('user_items/<str:error>', views.user_items, name='user_items'),
    path('user_items', views.user_items, name='user_items'),
    path('add_item', views.add_item, name='add_item'),
    path('buy_item', views.buy_item, name='buy_item'),
    path('remove_item', views.remove_item, name='remove_item')
]