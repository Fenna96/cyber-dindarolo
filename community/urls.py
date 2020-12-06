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

app_name = 'community'
urlpatterns = [
    path('profile/<str:username>', views.community_profile, name = 'community_profile'),
    path('modify/<str:email_error>', views.modify, name='modify'),
    path('modify/', views.modify, name='modify'),
    path('change_profile/', views.change_profile, name='change'),
    path('change_pic/', views.change_pic, name='change_pic'),
    path('search_user/', views.search_user, name ='search_user'),
    path('search/<str:error>', views.search_page, name ='search'),
    path('search/', views.search_page, name ='search'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('',views.index, name = 'index'),
]
