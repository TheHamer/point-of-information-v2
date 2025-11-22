import django_filters
from django_filters import CharFilter, DateFilter
from .models import Calendar
from django import forms


class FilterCalendar(django_filters.FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains", label="Name")
    location = CharFilter(field_name="location", lookup_expr="icontains", label="Location")
    start_date = DateFilter(field_name="startdate", lookup_expr="gte", label="Starts After")
    end_date = DateFilter(field_name="enddate", lookup_expr="lte", label="Ends Before")

    required_css_class = "test"

    class Meta:
        model = Calendar
        fields = '__all__' 
        exclude = ["tab", "enddate", "startdate", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["name"].field.widget.attrs.update({'class': 'serch-feild-text'})
        self.filters["location"].field.widget.attrs.update({'class': 'serch-feild-text'})
        self.filters["start_date"].field.widget.attrs.update({'class': 'serch-feild-text'})
        self.filters["end_date"].field.widget.attrs.update({'class': 'serch-feild-text'})
        self.filters["type"].field.widget.attrs.update({'class': 'serch-feild-select'})
        self.filters["region"].field.widget.attrs.update({'class': 'serch-feild-select'})
        self.filters["circuit"].field.widget.attrs.update({'class': 'serch-feild-select'})
        self.filters["online"].field.widget.attrs.update({'class': 'serch-feild-select'})
