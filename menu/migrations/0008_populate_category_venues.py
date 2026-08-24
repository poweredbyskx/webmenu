from django.db import migrations


def populate_venues(apps, schema_editor):
    Category = apps.get_model("menu", "Category")
    for category in Category.objects.exclude(venue__isnull=True):
        category.venues.add(category.venue_id)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0007_category_venues_m2m'),
    ]

    operations = [
        migrations.RunPython(populate_venues, reverse_noop),
    ]
