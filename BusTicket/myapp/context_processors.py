from .models import Route

def route_choices(request):
    origins = Route.objects.values_list('origin', flat=True).distinct()
    destinations = Route.objects.values_list('destination', flat=True).distinct()
    return {
        'origins': origins,
        'destinations': destinations
    }
