from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import file_views
from . import views

app_name = "api"
urlpatterns = [
    # User
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("registration/", views.Registration.as_view(), name="logout"),
    path("token/", views.Token.as_view(), name="token"),
    # Navbar
    path("navbar/", views.Navbar.as_view(), name="navbar"),
    # Manager
    path("manager/", views.Manager.as_view(), name="manager"),
    # Market
    path("market/insert/", views.Insert.as_view(), name="insert"),
    path("market/catalog/", views.Catalog.as_view(), name="catalog"),
    path("market/user_items/", views.UserItems.as_view(), name="user_items"),
    path("market/buy_item/", csrf_exempt(views.Buy.as_view()), name="buy_item"),
    path("market/remove_item/", views.Remove.as_view(), name="remove_item"),
    # Community
    path(
        "community/leaderboard/",
        file_views.leaderboardAPI.as_view(),
        name="leaderboard",
    ),
    path(
        "community/profile/<str:username>/",
        file_views.profileAPI.as_view(),
        name="profile",
    ),
    path(
        "community/search_user/", file_views.searchUserAPI.as_view(), name="search_user"
    ),
    path("community/modify/", file_views.modifyAPI.as_view(), name="modify"),
    # Analytics
    path("analytics/history/", file_views.historyAPI.as_view(), name="history"),
    path(
        "analytics/tracker=<str:item>",
        file_views.priceTrackerAPI.as_view(),
        name="price_tracker",
    ),
    path(
        "analytics/search_product/",
        file_views.searchProductAPI.as_view(),
        name="search_product",
    ),
]
