from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.
class Speaks(models.Model):

    TEAM_POSITIONS = [
        ("OG", "OG"),
        ("OO", "OO"),
        ("CG", "CG"),
        ("CO", "CO")
    ]

    SPEAKER_POSITIONS = [
        ("PM", "PM"),
        ("DPM", "DPM"),
        ("LO", "LO"),
        ("DLO", "DLO"),
        ("MG", "MG"),
        ("GW", "GW"),
        ("MO", "MO"),
        ("OW", "OW")
    ]

    TEAM_POINTS = [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3)
    ]

    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name="speaks")
    date = models.DateField(null=True, blank=True)
    tournament = models.CharField(max_length=50, null=True)
    partner = models.CharField(max_length=50, null=True, blank=True)
    round = models.PositiveIntegerField(null=True, blank=True)
    room_points = models.PositiveIntegerField(null=True, blank=True)
    team_position = models.CharField(max_length=2, null=True, blank=True, choices=TEAM_POSITIONS)
    speaker_position = models.CharField(max_length=3, null=True, blank=True, choices=SPEAKER_POSITIONS)
    motion_type = models.CharField(max_length=50, null=True, blank=True)
    motion = models.TextField(max_length=500, null=True, blank=True)
    info_slide = models.TextField(max_length=1000, null=True, blank=True)
    team_points = models.PositiveIntegerField(null=True, choices=TEAM_POINTS)
    speaker_score = models.PositiveIntegerField(null=True, validators=[MinValueValidator(50), MaxValueValidator(100)])
    include = models.BooleanField(default=True)