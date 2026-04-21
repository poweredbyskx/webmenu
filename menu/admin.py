import menu.translation

from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from modeltranslation.admin import TranslationAdmin
from .models import Category, Item


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