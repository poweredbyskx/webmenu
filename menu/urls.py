from django.urls import path
from .views import HomeView, MenuView, CategoryView, SearchView, RoastedView, BeansView, search_api

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("menu/", MenuView.as_view(), name="menu"),
    path("menu/<slug:slug>/", CategoryView.as_view(), name="category"),
    path("search/", SearchView.as_view(), name="search"),
    path("roasted/", RoastedView.as_view(), name="roasted"),
    path("beans/", BeansView.as_view(), name="beans"),

    path("api/search/", search_api, name="search_api"),
]