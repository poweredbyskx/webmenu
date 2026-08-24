from . import translation  # noqa: F401

from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from modeltranslation.admin import TranslationAdmin
from .models import Category, Item, RoastedCoffee, Venue


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, TranslationAdmin):
    list_display = ("name", "slug", "get_venues", "order")
    list_filter = ("venues",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("venues",)

    def get_venues(self, obj):
        return ", ".join(v.name for v in obj.venues.all())
    get_venues.short_description = "Заведения"


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


@admin.register(Venue)
class VenueAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}