from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = "api"
urlpatterns = [
    # User
    path("login/", views.loginAPI.as_view(), name="login"),
    path("logout/", views.logoutAPI.as_view(), name="logout"),
    path("registration/", views.registrationAPI.as_view(), name="logout"),
    path("token/", views.tokenAPI.as_view(), name="token"),
    # Navbar
    path("navbar/", views.navbarAPI.as_view(), name="navbar"),
    # Manager
    path("manager/", views.managerAPI.as_view(), name="manager"),
    # Market
    path("market/insert/", views.insertAPI.as_view(), name="insert"),
    path("market/catalog/", views.catalogAPI.as_view(), name="catalog"),
    path("market/user_items/", views.user_itemsAPI.as_view(), name="user_items"),
    path("market/buy_item/", csrf_exempt(views.buyAPI.as_view()), name="buy_item"),
    path("market/remove_item/", views.removeAPI.as_view(), name="remove_item"),
    # Community
    path("community/leaderboard/", views.leaderboardAPI.as_view(), name="leaderboard"),
    path(
        "community/profile/<str:username>/", views.profileAPI.as_view(), name="profile"
    ),
    path("community/search_user/", views.searchUserAPI.as_view(), name="search_user"),
    path("community/modify/", views.modifyAPI.as_view(), name="modify"),
    # Analytics
    path("analytics/history/", views.historyAPI.as_view(), name="history"),
    path(
        "analytics/tracker=<str:item>",
        views.priceTrackerAPI.as_view(),
        name="price_tracker",
    ),
    path(
        "analytics/search_product/",
        views.searchProductAPI.as_view(),
        name="search_product",
    ),
]
