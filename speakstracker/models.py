import json
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError


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
    tournament_url = models.URLField(max_length=500, null=True, blank=True, help_text="URL of the competition homepage if imported from a link")
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
    
    # Full call (all 4 teams in rank order, stored as JSON list: ["OO", "OG", "CO", "CG"])
    call = models.TextField(null=True, blank=True, help_text="JSON list of all 4 teams in rank order (1st to 4th)")
    
    def get_call_list(self):
        """Get the full call as a Python list."""
        if not self.call:
            return []
        try:
            return json.loads(self.call)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_call_list(self, positions):
        """Set the full call from a Python list."""
        if positions:
            self.call = json.dumps(positions)
        else:
            self.call = None
    
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
        Get the call (team ranking) formatted as "[team 1] [team 2] [team 3] [team 4]".
        The furthest left team is first place.
        """
        call_list = self.get_call_list()
        
        # call should contain the full call (4 teams in rank order)
        if len(call_list) == 4:
            return " ".join(call_list)
        
        # If we don't have the full call (4 teams), return None
        return None
    
    def clean(self):
        """
        Validate that speaker position matches team position and points align with call.
        Note: This validation is primarily handled in the form for better user experience.
        This method is kept for programmatic saves that bypass the form.
        """
        # Validation 1: Speaker position must match team position
        if self.team_position and self.speaker_position:
            # Mapping of team positions to valid speaker positions
            team_to_speaker_map = {
                'OG': ['PM', 'DPM'],
                'OO': ['LO', 'DLO'],
                'CG': ['MG', 'GW'],
                'CO': ['MO', 'OW']
            }
            
            valid_speaker_positions = team_to_speaker_map.get(self.team_position, [])
            if self.speaker_position not in valid_speaker_positions:
                raise ValidationError({
                    'speaker_position': f"Speaker position '{self.speaker_position}' is not valid for team position '{self.team_position}'. "
                                     f"Valid positions for {self.team_position} are: {', '.join(valid_speaker_positions)}."
                })
        
        # Validation 2: Points must align with call
        if self.team_position and self.team_points is not None:
            call_list = self.get_call_list()
            
            # Only validate if we have a full call (4 teams)
            if isinstance(call_list, list) and len(call_list) == 4:
                if self.team_position not in call_list:
                    # Team position not in call - this is handled by form validation
                    return
                
                # Find the position of the team in the call (0 = 1st, 1 = 2nd, 2 = 3rd, 3 = 4th)
                team_index = call_list.index(self.team_position)
                # Map index to expected points: 0->3, 1->2, 2->1, 3->0
                expected_points = 3 - team_index
                
                if self.team_points != expected_points:
                    rank_names = ['1st', '2nd', '3rd', '4th']
                    call_str = ' '.join(call_list)
                    raise ValidationError({
                        'team_points': f"Team points ({self.team_points}) do not match your position in the call. "
                                     f"You are {rank_names[team_index]} place (call: {call_str}), "
                                     f"so you should have {expected_points} points."
                    })
    
    class Meta:
        verbose_name_plural = "Speaks"