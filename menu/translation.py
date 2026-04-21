from modeltranslation.translator import TranslationOptions, register
from .models import Category, Item

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)

@register(Item)
class ItemTranslationOptions(TranslationOptions):
    fields = ("name", "description")