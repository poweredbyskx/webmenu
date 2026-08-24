from django.db import migrations

SHARED_BAR_CATEGORY_SLUGS = ["kofe", "ne-kofe", "kholodnyi-kofe", "kokteili"]


def set_venue_data(apps, schema_editor):
    Venue = apps.get_model("menu", "Venue")
    Category = apps.get_model("menu", "Category")

    # Исходная (единственная до разделения) точка могла остаться под разным
    # slug на разных окружениях из-за истории миграций (см. комментарии в
    # 0006) — находим её как "не kakao_gaudan", а не по конкретному slug.
    mir4 = Venue.objects.exclude(slug="kakao_gaudan").first()
    if mir4 is not None:
        mir4.slug = "kakao_mir4"
        mir4.name = "Мир 4"
        mir4.address = "Мир 4, Parahat базар"
        mir4.phone = "+99364359786"
        mir4.google_maps_url = "https://maps.app.goo.gl/XEjLdNFKJqW7418j9"
        mir4.apple_maps_url = "https://maps.apple.com/?ll=37.897551,58.394592&q=Kakao.breakfast"
        mir4.save()

    gaudan, _ = Venue.objects.get_or_create(
        slug="kakao_gaudan", defaults={"name": "Гаудане"}
    )
    gaudan.name = "Гаудане"
    gaudan.address = "Гаудан А"
    gaudan.phone = "+99365089922"
    gaudan.google_maps_url = "https://maps.app.goo.gl/RD43R6MVyKRoYtb56"
    gaudan.apple_maps_url = (
        "https://maps.apple.com/place?map=explore&address=Howdan+A%2C+"
        "%D0%A2%D1%83%D1%80%D0%BA%D0%BC%D0%B5%D0%BD%D0%B8%D1%81%D1%82%D0%B0%D0%BD"
        "&coordinate=37.916523%2C58.401058&name=Howdan+A"
    )
    gaudan.save()

    # Барное меню одинаковое на обеих точках — расшариваем эти категории
    # на Гаудан, не дублируя записи.
    if mir4 is not None:
        for slug in SHARED_BAR_CATEGORY_SLUGS:
            category = Category.objects.filter(slug=slug).first()
            if category is not None:
                category.venues.add(gaudan)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0011_venue_contact_fields'),
    ]

    operations = [
        migrations.RunPython(set_venue_data, reverse_noop),
    ]
