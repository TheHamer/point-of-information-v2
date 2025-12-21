import json
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class Speaks(models.Model):
    """Model to store speaker scores and round information."""

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
    
    # Points-to-position mapping for win rate calculations
    POINTS_TO_RANK = {3: 1, 2: 2, 1: 3, 0: 4}

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
    
    # Opponent positions in the same room (stored as JSON list: ["OO", "CG", "CO"])
    opponent_positions = models.TextField(null=True, blank=True, help_text="JSON list of opponent team positions")
    
    def get_opponent_positions_list(self):
        """Get opponent positions as a Python list."""
        if not self.opponent_positions:
            return []
        try:
            return json.loads(self.opponent_positions)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_opponent_positions_list(self, positions):
        """Set opponent positions from a Python list."""
        if positions:
            self.opponent_positions = json.dumps(positions)
        else:
            self.opponent_positions = None
    
    @property
    def average_points_so_far(self):
        """
        Calculate average points so far (cumulative team points / round number - 1).
        
        For round 1, returns 1.5 (exactly average).
        """
        if self.round is None or self.round == 1:
            return 1.5
        if self.room_points is None:
            return 1.5
        return self.room_points / (self.round - 1)
    
    @property
    def rank_in_round(self):
        """Get the rank (1st-4th) in this round based on team points."""
        if self.team_points is None:
            return None
        return self.POINTS_TO_RANK.get(self.team_points)
    
    def get_call(self):
        """
        Get the call (team ranking) formatted as "[team 1]>[team 2]>[team 3]>[team 4]".
        The furthest left team is first place.
        """
        if self.team_position is None or self.team_points is None:
            return None
        
        opponent_positions = self.get_opponent_positions_list()
        
        # opponent_positions should contain the full call (4 teams in rank order)
        if len(opponent_positions) == 4:
            return " ".join(opponent_positions)
        
        # If we don't have the full call (4 teams), return None
        return None
    
    class Meta:
        verbose_name_plural = "Speaks"