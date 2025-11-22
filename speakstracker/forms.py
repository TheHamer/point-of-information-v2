from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django import forms
from django.contrib.auth.models import User

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
        labels = {'tournament': 'Tournament*', 'team_points': 'Team points*', 'speaker_score': 'Speaker score*'}
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
        }

class EnterTabURL(forms.Form):
    tab_url = forms.CharField(label="Tab URL*", max_length=500, widget=forms.TextInput(attrs={'class': 'enter-speaks-field'}))
    name = forms.CharField(label="Name*", max_length=200, widget=forms.TextInput(attrs={'class': 'enter-speaks-field'}))
    date = forms.DateField(label="Date", required=False, widget=forms.TextInput(attrs={'class': 'enter-speaks-field', 'type': 'date'}))
    tournament = forms.CharField(label="Tournament*", max_length=200, widget=forms.TextInput(attrs={'class': 'enter-speaks-field'}))