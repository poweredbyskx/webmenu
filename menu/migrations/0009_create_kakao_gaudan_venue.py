from django.db import migrations


def create_venue(apps, schema_editor):
    Venue = apps.get_model("menu", "Venue")
    Venue.objects.get_or_create(
        slug="kakao_gaudan",
        defaults={"name": "Какао Гаудан"},
    )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0008_populate_category_venues'),
    ]

    operations = [
        migrations.RunPython(create_venue, reverse_noop),
    ]
