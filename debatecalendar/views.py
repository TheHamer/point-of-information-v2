from django.shortcuts import render
from .models import Calendar
from django.http import HttpResponse
from .filters import FilterCalendar

# Create your views here.

def calendar(request):
    calendar_items = Calendar.objects.all().values()

    filtered = FilterCalendar(request.GET, queryset=calendar_items)
    calendar_items = filtered.qs

    for comp in calendar_items:
        comp.pop("id")

    context = {"calendar_items": calendar_items, "filter": filtered}

    return render(request, "debatecalendar/calendar.html", context)