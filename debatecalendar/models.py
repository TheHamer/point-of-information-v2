from django.db import models

# Create your models here.
class Calendar(models.Model):

    REGOION_CHOICES = [
        ("Asia", "Asia"), 
        ("europe", "europe"), 
        ("North America", "North America"),
        ("Latin America", "Latin America"),
        ("Australasia", "Australasia")
    ]

    CIRCUIT_CHOICES = [
        ("IoNA", "IoNA"),
        ("Netherlands", "Netherlands"),
        ("Bulkans", "Bulkans")
    ]

    TYPE_CHOICES = [
        ("Open", "Open"),
        ("IV", "IV"),
        ("Schools", "Schools"),
        ("Juniors", "Juniors"),
        ("Pro-am", "Pro-am"),
        ("Noives", "Noives"),
        ("Unknown", "Unknown"),
    ]

    name = models.CharField(max_length=200, null=True)
    type = models.CharField(max_length=50, null=True, choices=TYPE_CHOICES)
    startdate = models.DateField(null=True)
    enddate = models.DateField(null=True)
    timezone = models.CharField(max_length=50, null=True)
    region = models.CharField(max_length=50, null=True, choices=REGOION_CHOICES)
    circuit = models.CharField(max_length=50, null=True, choices=CIRCUIT_CHOICES)
    online = models.BooleanField(null=True)
    location = models.CharField(max_length=50, null=True)
    tab = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name