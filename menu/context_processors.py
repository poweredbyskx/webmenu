from .models import Category

def menu_categories(request):
    venue_slug = request.session.get("venue_slug")
    qs = Category.objects.all()
    if venue_slug:
        qs = qs.filter(venues__slug=venue_slug).distinct()
    return {"menu_categories": qs.order_by("order", "name")}
