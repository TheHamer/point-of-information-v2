from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django import forms
from django.forms import models as forms_models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import json

from .models import Speaks

class CreateUserForm(UserCreationForm):

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class':'password-username', 'type':'password', 'placeholder':'Password'}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={'class':'password-username', 'type':'password', 'placeholder':'Confirm Password'}),
    )

    class Meta:

        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'password-username', 'placeholder': 'Username'}),
            'email': forms.TextInput(attrs={'class': 'password-username', 'placeholder': 'Email'}),
        }

class changeUserDetails(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'password-username', 'placeholder': 'Username'}),
            'email': forms.TextInput(attrs={'class': 'password-username', 'placeholder': 'Email'}),
        }

class PasswordChange(PasswordChangeForm):
    old_password = forms.CharField(
        label='Old password',
        widget=forms.PasswordInput(attrs={'class': 'password-username', 'placeholder': 'Old password'}),
    )
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'password-username', 'placeholder': 'New password'}),
    )
    new_password2 = forms.CharField(
        label='New password confirm',
        widget=forms.PasswordInput(attrs={'class': 'password-username', 'placeholder': 'Confirm new password'}),
    )

class PasswordReset(PasswordResetForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'password-username', 'placeholder': 'Email'}))

class SetPassword(SetPasswordForm):
    new_password1 = forms.CharField(
        label='new password',
        widget=forms.PasswordInput(attrs={'class': 'password-username', 'placeholder': 'New password'}),
    )
    new_password2 = forms.CharField(
        label='new password confirm',
        widget=forms.PasswordInput(attrs={'class': 'password-username', 'placeholder': 'Confirm new password'}),
    )

class EnterSpeaks(ModelForm):

    class Meta:
        model = Speaks
        exclude = ["user", "include"]
        labels = {
            'tournament': 'Tournament*', 
            'tournament_url': 'Tournament URL',
            'team_points': 'Team points*', 
            'speaker_score': 'Speaker score*',
            'opponent_positions': 'Full call'
        }
        widgets = {
            'date': forms.DateInput(attrs={'class': 'enter-speaks-field', 'type': 'date'}),
            'tournament': forms.TextInput(attrs={'class': 'enter-speaks-field'}),
            'tournament_url': forms.TextInput(attrs={'class': 'enter-speaks-field'}),
            'partner': forms.TextInput(attrs={'class': 'enter-speaks-field'}),
            'motion_type': forms.TextInput(attrs={'class': 'enter-speaks-field'}),
            'round': forms.NumberInput(attrs={'class': 'enter-speaks-field'}),
            'room_points': forms.NumberInput(attrs={'class': 'enter-speaks-field'}),
            'speaker_score': forms.NumberInput(attrs={'class': 'enter-speaks-field'}),
            'team_position': forms.Select(attrs={'class': 'enter-speaks-select'}),
            'speaker_position': forms.Select(attrs={'class': 'enter-speaks-select'}),
            'team_points': forms.Select(attrs={'class': 'enter-speaks-select'}),
            'motion': forms.TextInput(attrs={'class': 'enter-speaks-field'}),
            'info_slide': forms.TextInput(attrs={'class': 'enter-speaks-field'}),
            'opponent_positions': forms.TextInput(attrs={
                'class': 'enter-speaks-field',
                'placeholder': 'e.g., OO OG CO CG'
            }),
        }
        help_texts = {
            'opponent_positions': 'Enter call separated by spaces (e.g., OO OG CO CG)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing instance, use get_call() to populate the field
        if self.instance and self.instance.pk:
            call = self.instance.get_call()
            if call:
                self.initial['opponent_positions'] = call

    def clean_opponent_positions(self):
        """Parse full call input and validate it contains exactly 4 teams."""
        full_call = self.cleaned_data.get('opponent_positions', '').strip()
        
        if not full_call:
            return None
        
        # Parse space-separated full call
        positions = [pos.strip().upper() for pos in full_call.split() if pos.strip()]
        
        # Validate we have exactly 4 teams
        if len(positions) != 4:
            raise forms.ValidationError(
                f"Full call must contain exactly 4 teams (1st, 2nd, 3rd, 4th). "
                f"You entered {len(positions)} team(s)."
            )
        
        # Validate positions are valid team positions
        valid_positions = ['OG', 'OO', 'CG', 'CO']
        invalid_positions = [pos for pos in positions if pos not in valid_positions]
        
        if invalid_positions:
            raise forms.ValidationError(
                f"Invalid team positions: {', '.join(invalid_positions)}. "
                f"Valid positions are: {', '.join(valid_positions)}"
            )
        
        # Check for duplicates
        if len(positions) != len(set(positions)):
            raise forms.ValidationError(
                "Full call contains duplicate team positions. Each team should appear exactly once."
            )
        
        # Verify all 4 required teams are present exactly once
        positions_set = set(positions)
        required_teams = set(valid_positions)
        if positions_set != required_teams:
            missing_teams = required_teams - positions_set
            extra_teams = positions_set - required_teams
            error_parts = []
            if missing_teams:
                error_parts.append(f"Missing teams: {', '.join(sorted(missing_teams))}")
            if extra_teams:
                error_parts.append(f"Invalid teams: {', '.join(sorted(extra_teams))}")
            raise forms.ValidationError(
                f"Full call must contain exactly one of each team (OG, OO, CG, CO). "
                f"{' '.join(error_parts)}"
            )
        
        # Store the full call temporarily (will be processed in clean method)
        # We'll store it as JSON for now, but clean() will extract opponents
        return json.dumps(positions)
    
    def clean(self):
        """Extract opponent positions from full call after validating team_position."""
        cleaned_data = super().clean()
        full_call_json = cleaned_data.get('opponent_positions')
        team_position = cleaned_data.get('team_position')
        speaker_position = cleaned_data.get('speaker_position')
        team_points = cleaned_data.get('team_points')
        
        # Validation 1: Speaker position must match team position
        if team_position and speaker_position:
            # Mapping of team positions to valid speaker positions
            team_to_speaker_map = {
                'OG': ['PM', 'DPM'],
                'OO': ['LO', 'DLO'],
                'CG': ['MG', 'GW'],
                'CO': ['MO', 'OW']
            }
            
            valid_speaker_positions = team_to_speaker_map.get(team_position, [])
            if speaker_position not in valid_speaker_positions:
                raise forms.ValidationError({
                    'speaker_position': f"Speaker position '{speaker_position}' is not valid for team position '{team_position}'. "
                                     f"Valid positions for {team_position} are: {', '.join(valid_speaker_positions)}."
                })
        
        if not full_call_json:
            return cleaned_data
        
        # Parse the full call
        try:
            full_call = json.loads(full_call_json)
        except (json.JSONDecodeError, TypeError) as e:
            raise forms.ValidationError({
                'opponent_positions': f"Invalid format: {str(e)}"
            })
        
        # If we have a full call (4 teams) and a team_position, validate and store the full call
        if isinstance(full_call, list) and len(full_call) == 4 and team_position:
            # Validate that user's team is in the full call
            if team_position not in full_call:
                raise forms.ValidationError({
                    'opponent_positions': f"Your team position ({team_position}) must be included in the full call."
                })
            
            # Validation 2: Points must align with call
            if team_points is not None:
                # Find the position of the team in the call (0 = 1st, 1 = 2nd, 2 = 3rd, 3 = 4th)
                team_index = full_call.index(team_position)
                # Map index to expected points: 0->3, 1->2, 2->1, 3->0
                expected_points = 3 - team_index
                
                if team_points != expected_points:
                    rank_names = ['1st', '2nd', '3rd', '4th']
                    raise forms.ValidationError({
                        'team_points': f"Team points ({team_points}) do not match your position in the call. "
                                     f"You are {rank_names[team_index]} place (call: {' '.join(full_call)}), "
                                     f"so you should have {expected_points} points."
                    })
            
            # Store the full call (all 4 teams in rank order) - get_call() will use it directly
            cleaned_data['opponent_positions'] = json.dumps(full_call)
        
        return cleaned_data
    
    def _post_clean(self):
        """
        Override to prevent duplicate validation errors.
        We handle all validation in clean(), so we skip the model's clean() method
        to avoid duplicate error messages.
        """
        opts = self._meta
        exclude = self._get_validation_exclusions()
        
        # Update the instance with cleaned data
        try:
            self.instance = forms_models.construct_instance(
                self, self.instance, opts.fields, opts.exclude
            )
        except ValidationError as e:
            self._update_errors(e)
        
        # Skip calling instance.full_clean() to avoid duplicate validation errors
        # since we've already validated everything in clean()
        # We only validate unique constraints
        if self._validate_unique:
            self.validate_unique()

class EnterTabURL(forms.Form):
    """Form for importing tournament data from Tabbycat URL or API."""
    
    tab_url = forms.CharField(
        label="Tab URL*", 
        max_length=500, 
        widget=forms.TextInput(attrs={'class': 'enter-speaks-field', 'placeholder': 'https://tabbycat.example.com/tournament/'})
    )
    name = forms.CharField(
        label="Speaker Name*", 
        max_length=200, 
        widget=forms.TextInput(attrs={'class': 'enter-speaks-field', 'placeholder': 'Your name as it appears on tab'})
    )
    date = forms.DateField(
        label="Tournament Date", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'enter-speaks-field', 'type': 'date'})
    )
    tournament = forms.CharField(
        label="Tournament Name*", 
        max_length=200, 
        widget=forms.TextInput(attrs={'class': 'enter-speaks-field', 'placeholder': 'e.g., EUDC 2024'})
    )