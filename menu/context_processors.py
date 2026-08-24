from .models import Category, Venue

def menu_categories(request):
    venue_slug = request.session.get("venue_slug")
    qs = Category.objects.all()
    if venue_slug:
        qs = qs.filter(venues__slug=venue_slug).distinct()
    return {"menu_categories": qs.order_by("order", "name")}

def current_venue(request):
    venue_slug = request.session.get("venue_slug")
    venue = Venue.objects.filter(slug=venue_slug).first() if venue_slug else None
    return {"current_venue": venue}
