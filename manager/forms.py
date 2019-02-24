from django.contrib.auth.forms import UserCreationForm

from django.forms import ModelForm
from django import forms
from .models import *
from django.db import models

class MainConfigurationForm(ModelForm):
    class Meta:
        model = MainConfiguration
        fields = ['team_name', 'intro_message', 'cpu_ratio', 'ram_ratio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'id':field,
                'rows':'1',
                'autocomplete':'none'
        })



class AddUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username',  'password1', 'password2', 'email', 'role', 'special']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'id':field,
                'autocomplete':'none'
        })
