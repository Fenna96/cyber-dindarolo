"""martistupe URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from . import views

app_name = 'analytics'
urlpatterns = [
    path('history', views.history, name='history'),
    path('tracker=<str:item>', views.price_tracker, name='price_tracker'),
    path('search_product/', views.search_product, name='search_product'),
    path('search/<str:error>', views.search_page, name='search'),
    path('search/', views.search_page, name='search'),
    path('',views.index, name = 'index'),
]
