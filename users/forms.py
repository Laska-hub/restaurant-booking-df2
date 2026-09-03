from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
        )
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Email",
        }
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"},
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"},
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"},
            ),
        }
