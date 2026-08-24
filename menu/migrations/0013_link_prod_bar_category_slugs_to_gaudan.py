from django.db import migrations

# 0012 линковало общие категории бара на kakao_gaudan по slug'ам из локальной
# dev-базы (kofe/ne-kofe/kholodnyi-kofe/kokteili — автотранслит с русского).
# На проде у этих же категорий slug другой (задан вручную через админку в
# своё время): coffee/non_coffee/ice_coffee/cocktails — ровно то, что уже
# годами используется в views.DRINK_CATEGORY_SLUGS. Из-за этого расхождения
# 0012 на проде тихо ничего не нашла и не привязала Гаудан к бару.
PROD_BAR_CATEGORY_SLUGS = ["coffee", "non_coffee", "ice_coffee", "cocktails"]


def link_prod_bar_categories(apps, schema_editor):
    Venue = apps.get_model("menu", "Venue")
    Category = apps.get_model("menu", "Category")

    gaudan = Venue.objects.filter(slug="kakao_gaudan").first()
    if gaudan is None:
        return

    for slug in PROD_BAR_CATEGORY_SLUGS:
        category = Category.objects.filter(slug=slug).first()
        if category is not None:
            category.venues.add(gaudan)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0012_venue_data_and_shared_bar_categories'),
    ]

    operations = [
        migrations.RunPython(link_prod_bar_categories, reverse_noop),
    ]
