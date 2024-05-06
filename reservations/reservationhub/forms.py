from django import forms
from django.db import models
from .models import Reservation
from .models import Passager
from django.contrib.auth.forms import UserCreationForm
from .models import Client
from django.contrib.auth.models import User

class ReservationForm(forms.ModelForm):
    numero_place = forms.IntegerField(min_value=1, max_value=200)

    class Meta:
        model = Reservation
        fields = ['date_reservation', 'numero_reservation', 'numero_place', 'passager']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_reservation'].widget.attrs['readonly'] = True
        self.fields['numero_reservation'].widget.attrs['readonly'] = True
        

class PassagerForm(forms.ModelForm):
    class Meta:
        model = Passager
        fields = ['nom', 'prenom', 'date_naissance']
        # Spécifiez le format de date souhaité
        input_formats = ['%d/%m/%Y']


class CustomUserCreationForm(UserCreationForm):
    adresse = forms.CharField(max_length=255)
    telephone = forms.CharField(max_length=20)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            Client.objects.create(user=user, adresse=self.cleaned_data['adresse'], telephone=self.cleaned_data['telephone'])
        return user