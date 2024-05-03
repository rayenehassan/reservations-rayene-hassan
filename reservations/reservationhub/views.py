from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Trajet, Gare, Reservation, Client, Passager
from .forms import ReservationForm
from datetime import datetime
import random
from django.utils.crypto import get_random_string
from .forms import PassagerForm
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.contrib.auth import login

from django.db.models import Count

# Create your views here.

def trajets(request):
    trajets_disponibles = Trajet.objects.all()
    gares_disponibles = Gare.objects.all()

    if request.method == 'GET':
        gare_depart_id = request.GET.get('gare_depart')
        gare_arrivee_id = request.GET.get('gare_arrivee')

        if gare_depart_id:
            gare_depart = get_object_or_404(Gare, pk=gare_depart_id)
            trajets_disponibles = trajets_disponibles.filter(gare_depart=gare_depart)
        if gare_arrivee_id:
            gare_arrivee = get_object_or_404(Gare, pk=gare_arrivee_id)
            trajets_disponibles = trajets_disponibles.filter(gare_arrivee=gare_arrivee)

    return render(request, 'reservationhub/trajets.html', {'trajets': trajets_disponibles, 'gares': gares_disponibles})

def mes_reservations(request):
    if request.user.is_authenticated:
        client = Client.objects.get(user=request.user)
        reservations = Reservation.objects.filter(utilisateur_reservation=client)
        return render(request, 'reservationhub/mes_reservations.html', {'reservations': reservations})
    else:
        return render(request, 'reservationhub/mes_reservations.html', {})



def edit_reservation(request, trajet_id):
    utilisateur = request.user
    client = Client.objects.get(user=utilisateur)  
    trajet = Trajet.objects.get(id=trajet_id)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.trajet = trajet
            reservation.utilisateur_reservation = client  
            reservation.date_reservation = datetime.now()
            reservation.numero_place = random.randint(1, 200)
            reservation.numero_reservation = get_random_string(length=8, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            reservation.save()
            return redirect('reservationhub:mes_reservations')
    else:
        passagers_disponibles = Passager.objects.filter(utilisateur=request.user)
        
        initial_data = {
            'date_reservation': datetime.now().date(),
            'numero_place': random.randint(1, 200),
            'numero_reservation': get_random_string(length=8, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
        }
        form = ReservationForm(initial=initial_data)
        form.fields['passager'].queryset = passagers_disponibles
        
    return render(request, 'reservationhub/edit_reservation.html', {'form': form, 'trajet': trajet})


def creer_passager(request):
    utilisateur = request.user
    if request.method == 'POST':
        form = PassagerForm(request.POST)
        if form.is_valid():
            passager = form.save(commit=False)
            passager.utilisateur = utilisateur  
            passager.save()
            return redirect('reservationhub:trajets')
    else:
        form = PassagerForm()
    return render(request, 'reservationhub/creer_passager.html', {'form': form})


def modifier_reservation(request, reservation_id=None):
    utilisateur = request.user
    client = Client.objects.get(user=utilisateur)  
    
    
    if (reservation_id == None):
        reservation = None
    else:
        reservation = get_object_or_404(Reservation, id=reservation_id)
        # si l'user cherche à accéder à une réservation qui n'est pas la sienne
        if (reservation.client != client):
            return redirect('reservationhub:mes_reservations')

    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return redirect('reservationhub:mes_reservations')
    else:
        passagers_disponibles = Passager.objects.filter(utilisateur=request.user)
        form = ReservationForm(instance=reservation)
        form.fields['passager'].queryset = passagers_disponibles
        
    return render(request, 'reservationhub/modifier_reservation.html', {'form': form, 'reservation': reservation})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')  
    else:
        form = CustomUserCreationForm()
    return render(request, 'reservationhub/register.html', {'form': form})

def homepage(request):
    trajets_disponibles = Trajet.objects.all()
    gares_disponibles = Gare.objects.all()
    return render(request, 'reservationhub/homepage.html', {'trajets': trajets_disponibles, 'gares': gares_disponibles})

def homepage_connecte(request):
    if request.user.is_authenticated:
        trajets_disponibles = Trajet.objects.all()
        gares_disponibles = Gare.objects.all()
        return render(request, 'reservationhub/homepage_connecte.html', {'trajets': trajets_disponibles, 'gares': gares_disponibles})
    else:
        return render(request, 'reservationhub/homepage_connecte.html', {})


def recherche_reservations(request):
    gares_disponibles = Gare.objects.all()
    gare_name = request.GET.get('gare')

    reservations_depart = []
    reservations_arrivee = []

    if gare_name:
        gare_depart = Gare.objects.filter(nom=gare_name).first()
        if gare_depart:
            reservations_depart = Reservation.objects.filter(trajet__gare_depart=gare_depart)

        gare_arrivee = Gare.objects.filter(nom=gare_name).first()
        if gare_arrivee:
            reservations_arrivee = Reservation.objects.filter(trajet__gare_arrivee=gare_arrivee)

    context = {
        'gares_disponibles': gares_disponibles,
        'gare_name': gare_name,
        'reservations_depart': reservations_depart,
        'reservations_arrivee': reservations_arrivee,
    }
    return render(request, 'reservationhub/recherche_reservations.html', context)