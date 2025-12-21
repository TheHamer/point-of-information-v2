from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django import forms
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
            'team_points': 'Team points*', 
            'speaker_score': 'Speaker score*',
            'opponent_positions': 'Full call'
        }
        widgets = {
            'date': forms.DateInput(attrs={'class': 'enter-speaks-field', 'type': 'date'}),
            'tournament': forms.TextInput(attrs={'class': 'enter-speaks-field'}),
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
        
        # Check if it's already JSON (for backwards compatibility with old data)
        try:
            parsed = json.loads(full_call)
            if isinstance(parsed, list):
                # Old format: just return as-is
                return full_call
        except (json.JSONDecodeError, TypeError):
            pass
        
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
        
        # Store the full call temporarily (will be processed in clean method)
        # We'll store it as JSON for now, but clean() will extract opponents
        return json.dumps(positions)
    
    def clean(self):
        """Extract opponent positions from full call after validating team_position."""
        cleaned_data = super().clean()
        full_call_json = cleaned_data.get('opponent_positions')
        team_position = cleaned_data.get('team_position')
        
        if not full_call_json:
            return cleaned_data
        
        # Parse the full call
        try:
            full_call = json.loads(full_call_json)
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, it might be old format - leave as is
            return cleaned_data
        
        # If we have a full call (4 teams) and a team_position, validate and store the full call
        if isinstance(full_call, list) and len(full_call) == 4 and team_position:
            # Validate that user's team is in the full call
            if team_position not in full_call:
                raise forms.ValidationError({
                    'opponent_positions': f"Your team position ({team_position}) must be included in the full call."
                })
            
            # Store the full call (all 4 teams in rank order) - get_call() will use it directly
            cleaned_data['opponent_positions'] = json.dumps(full_call)
        
        return cleaned_data

class EnterTabURL(forms.Form):
    """Form for importing tournament data from Tabbycat URL or API."""
    
    DATA_SOURCE_CHOICES = [
        ('api', 'Use Tabbycat API (recommended)'),
        ('scraper', 'Use web scraping (legacy)'),
    ]
    
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
    data_source = forms.ChoiceField(
        label="Data Source",
        choices=DATA_SOURCE_CHOICES,
        initial='api',
        widget=forms.RadioSelect(attrs={'class': 'enter-speaks-radio'})
    )