from . import translation  # noqa: F401

from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from modeltranslation.admin import TranslationAdmin
from .models import Category, Item, RoastedCoffee


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, TranslationAdmin):
    list_display = ("name", "slug", "order")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Item)
class ItemAdmin(SortableAdminMixin, TranslationAdmin):
    list_display = ("name", "category", "price", "is_new", "is_seasonal", "order")
    list_filter = ("category", "is_new", "is_seasonal")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(RoastedCoffee)
class RoastedCoffeeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("name", "origin", "region", "weight", "price", "is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("name", "origin", "region", "flavor_notes")
    prepopulated_fields = {"slug": ("name",)}