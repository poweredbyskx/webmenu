from menu.models import Category, Venue


def make_venue(**kwargs):
    kwargs.setdefault("name", "Тестовое заведение")
    kwargs.setdefault("slug", "test-venue")
    venue, _ = Venue.objects.get_or_create(slug=kwargs["slug"], defaults=kwargs)
    return venue


def make_category(**kwargs):
    kwargs.setdefault("venue", make_venue())
    return Category.objects.create(**kwargs)
