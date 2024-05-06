from django.shortcuts import render, get_object_or_404, redirect
from .models import Trajet, Gare, Reservation, Client, Passager
from .forms import ReservationForm
from datetime import datetime
import random
from django.utils.crypto import get_random_string
from .forms import PassagerForm
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.contrib.auth import login

# Create your views here.

def construire_graphe_trajets(trajets):
    graphe = {}

    for trajet in trajets:
        gare_depart = trajet.gare_depart
        gare_arrivee = trajet.gare_arrivee
        duree_trajet = trajet.date_heure_arrivee - trajet.date_heure_depart

        if gare_depart not in graphe:
            graphe[gare_depart] = []

        graphe[gare_depart].append((gare_arrivee, duree_trajet))

    return graphe


def dijkstra(graphe, depart, arrivee):
    distances = {gare: float('inf') for gare in graphe}
    distances[depart] = 0
    precedents = {}
    non_visites = {gare: distances[gare] for gare in graphe}

    while non_visites:
        gare_actuelle = min(non_visites, key=non_visites.get)
        
        # Si la gare actuelle est la gare d'arrivée, arrêtez la boucle
        if gare_actuelle == arrivee:
            break
        
        for gare_suivante, duree in graphe.get(gare_actuelle, []):
            duree_minutes = duree.total_seconds() / 60
            nouvelle_distance = distances[gare_actuelle] + duree_minutes
            if nouvelle_distance < distances.get(gare_suivante, float('inf')):
                distances[gare_suivante] = nouvelle_distance
                precedents[gare_suivante] = gare_actuelle  
                non_visites[gare_suivante] = nouvelle_distance

        del non_visites[gare_actuelle]

    # Si aucune solution n'a été trouvée
    if arrivee not in precedents:
        return None

    chemin = []
    gare_actuelle = arrivee
    while gare_actuelle != depart:
        chemin.append(gare_actuelle)
        gare_actuelle = precedents[gare_actuelle]
    chemin.append(depart)
    chemin.reverse()

    return {'chemin': chemin, 'distance': distances[arrivee]}



from django.db.models import Q


def trajets(request):
    trajets_disponibles = Trajet.objects.all()
    gares_disponibles = Gare.objects.all()

    if request.method == 'GET':
        gare_depart_id = request.GET.get('gare_depart')
        gare_arrivee_id = request.GET.get('gare_arrivee')

        if gare_depart_id and gare_arrivee_id:
            gare_depart = get_object_or_404(Gare, pk=gare_depart_id)
            gare_arrivee = get_object_or_404(Gare, pk=gare_arrivee_id)

            trajets_optimaux = []

            for _ in range(3):  # Répéter trois fois pour trouver les trois trajets les plus courts
                graphe_trajets = construire_graphe_trajets(trajets_disponibles)
                resultats_dijkstra = dijkstra(graphe_trajets, gare_depart, gare_arrivee)

                if resultats_dijkstra is not None and 'chemin' in resultats_dijkstra:
                    trajet_courant = []
                    for i in range(len(resultats_dijkstra['chemin']) - 1):
                        trajet = Trajet.objects.filter(gare_depart=resultats_dijkstra['chemin'][i],
                                               gare_arrivee=resultats_dijkstra['chemin'][i + 1]).first()
                        trajet_courant.append(trajet)

                    trajets_optimaux.extend(trajet_courant)

                    # Supprimez les trajets optimaux des trajets disponibles pour la prochaine itération
                    trajets_disponibles = trajets_disponibles.exclude(pk__in=[trajet.pk for trajet in trajet_courant])

                else:
                    break  # S'il n'y a pas de solution, arrêtez la boucle

            if not trajets_optimaux:
                return render(request, 'reservationhub/trajets.html', {'trajets': [], 'gares': gares_disponibles})

            return render(request, 'reservationhub/trajets.html', {'trajets': trajets_optimaux, 'gares': gares_disponibles})

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


def modifier_reservation(request, reservation_id):
    utilisateur = request.user
    client = Client.objects.get(user=utilisateur)  

    reservation = get_object_or_404(Reservation, id=reservation_id)

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
    
    

    























