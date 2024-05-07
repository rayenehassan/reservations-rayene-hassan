from django.shortcuts import render, get_object_or_404, redirect
from .models import Trajet, Gare, Reservation, Client, Passager
from .forms import ReservationForm
from datetime import datetime
import random
from django.db.models.functions import TruncDate
from django.utils.crypto import get_random_string
from .forms import PassagerForm
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required


# imports de la section chartJS
from django.http import JsonResponse
from .charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict

from django.db.models import Count
from django.contrib.auth.decorators import login_required

# Create your views here.



def construire_graphe_trajets(trajets):
    """
    Cette fonction permet la création d'un dictionnaire avec comme clef les gares de départ des trajets, 
    et comme valeur associée à chaque clef, un tuple (gare d'arrivée, durée trajet).

    Args:
        trajets : un ou plusieurs trajets du modèle Trajet.

    Returns:
        graphe : renvoie le graphe des trajets sous forme de dictionnaire. 
    """
    
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
    """
    Cette fonction permet la recherche du chemin le plus court entre une gare de départ et une gare d'arrivée. 
    Le critère de recherche se base sur la somme des durées des trajets pour accéder à la gare d'arrivée.

    Args:
        graphe : graphe des trajets établis avec la fonction construire_graphe_trajets.
        depart : gare de départ.
        arrivee : gare d'arrivée.

    Returns:
        chemin : retourne le chemin le plus court (soit avec un trajet direct ou avec des correspondances) et la distance totale.
    """
    
    # Initialisation :
    distances = {gare: float('inf') for gare in graphe}
    distances[depart] = 0
    precedents = {}
    non_visites = {gare: distances[gare] for gare in graphe}

    while non_visites:
        gare_actuelle = min(non_visites, key=non_visites.get)       # Sélection de la gare non visitée la plus proche
        
        # Si la gare actuelle est la gare d'arrivée, arrêtez la boucle :
        if gare_actuelle == arrivee:
            break
        
        
        # Parcourir toutes les gares adjacentes à la gare actuelle :
        for gare_suivante, duree in graphe.get(gare_actuelle, []):
            duree_minutes = duree.total_seconds() / 60
            nouvelle_distance = distances[gare_actuelle] + duree_minutes
            if nouvelle_distance < distances.get(gare_suivante, float('inf')):      # Mettre à jour la distance si elle est plus courte que la précédente
                distances[gare_suivante] = nouvelle_distance
                precedents[gare_suivante] = gare_actuelle  
                non_visites[gare_suivante] = nouvelle_distance

        del non_visites[gare_actuelle]      # Marquer la gare actuelle comme visitée

    # Si aucune solution n'a été trouvée :
    if arrivee not in precedents:
        return None

    # Reconstituer le chemin à partir des gares précédentes :
    chemin = []
    gare_actuelle = arrivee
    while gare_actuelle != depart:
        chemin.append(gare_actuelle)
        gare_actuelle = precedents[gare_actuelle]
    chemin.append(depart)
    chemin.reverse()

    return {'chemin': chemin, 'distance': distances[arrivee]}



def trajets(request):
    """
    Cette vue permet d'afficher les trajets disponibles entre une gare de départ et une gare d'arrivée.
    Elle utilise l'algorithme de Dijkstra pour trouver les trajets les plus courts.
    
    Returns:
        HttpResponse : Retourne la page trajets.html avec les trajets optimaux ou tous les trajets disponibles.
    """

    # Initialisation :
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
                graphe_trajets = construire_graphe_trajets(trajets_disponibles)     # Construction du graphe des trajets disponibles (qui change à chaque itérations de la boucle)
                resultats_dijkstra = dijkstra(graphe_trajets, gare_depart, gare_arrivee)

                
                # Si une solution est trouvée :
                if resultats_dijkstra is not None and 'chemin' in resultats_dijkstra:
                    trajet_courant = []
                    for i in range(len(resultats_dijkstra['chemin']) - 1):      # Récupérer le trajet correspondant entre ces deux gares
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


import random, string
def generate_random_color():
    """
    Cette fonction permet de générer une couleur aléatoire en héxadécimal.
    """
    return '#' + ''.join(random.choices(string.hexdigits[:-6], k=6))


def trajets(request):
    """
    Cette vue permet d'afficher les trajets disponibles entre une gare de départ et une gare d'arrivée.
    Elle utilise l'algorithme de Dijkstra pour trouver les trajets les plus courts.
    
    Returns:
        HttpResponse : Retourne la page trajets.html avec les trajets optimaux ou tous les trajets disponibles.
    """

    # Initialisation :
    trajets_disponibles = Trajet.objects.all()
    gares_disponibles = Gare.objects.all()

    if request.method == 'GET':
        gare_depart_id = request.GET.get('gare_depart')
        gare_arrivee_id = request.GET.get('gare_arrivee')

        if gare_depart_id and gare_arrivee_id:
            gare_depart = get_object_or_404(Gare, pk=gare_depart_id)
            gare_arrivee = get_object_or_404(Gare, pk=gare_arrivee_id)
            # Stockage des noms des gares de départ et d'arrivée dans des variables : 
            nom_gare_depart = gare_depart.nom
            nom_gare_arrivee = gare_arrivee.nom

            trajets_optimaux = []

            for _ in range(3):  # Répéter trois fois pour trouver les trois trajets les plus courts
                graphe_trajets = construire_graphe_trajets(trajets_disponibles)     # Construction du graphe des trajets disponibles (qui change à chaque itérations de la boucle)
                resultats_dijkstra = dijkstra(graphe_trajets, gare_depart, gare_arrivee)

                # Si une solution est trouvée :
                if resultats_dijkstra is not None and 'chemin' in resultats_dijkstra:
                    trajets_solution = []
                    couleur_solution = generate_random_color()  # Générer une couleur aléatoire pour chaque solution

                    # Si la solution est un trajet avec correspondance : 
                    if len(resultats_dijkstra['chemin']) > 2:       
                        for i in range(len(resultats_dijkstra['chemin']) - 1):      # Récupérer le trajet correspondant entre ces deux gares
                            trajet = Trajet.objects.filter(gare_depart=resultats_dijkstra['chemin'][i],
                                gare_arrivee=resultats_dijkstra['chemin'][i + 1]).first()
                            trajet.correspondance = True
                            trajet.couleur_solution = couleur_solution  # Enregistrer la couleur attribuée à cette solution
                            trajets_solution.append(trajet)
                            
                    # Si la solution est un trajet direct :
                    else:
                        for i in range(len(resultats_dijkstra['chemin']) - 1):      # Récupérer le trajet correspondant entre ces deux gares
                            trajet = Trajet.objects.filter(gare_depart=resultats_dijkstra['chemin'][i],
                                gare_arrivee=resultats_dijkstra['chemin'][i + 1]).first()
                            trajet.correspondance = False
                            trajet.couleur_solution = couleur_solution  # Enregistrer la couleur attribuée à cette solution
                            trajets_solution.append(trajet)

                    trajets_optimaux.extend(trajets_solution)
                    # Supprimez les trajets optimaux des trajets disponibles pour la prochaine itération :
                    trajets_disponibles = trajets_disponibles.exclude(pk__in=[trajet.pk for trajet in trajets_solution])

                else:
                    break  # S'il n'y a pas de solution, arrêtez la boucle

            if not trajets_optimaux:
                return render(request, 'reservationhub/trajets.html', {'trajets': [], 'gares': gares_disponibles, 'nom_gare_depart': nom_gare_depart, 'nom_gare_arrivee': nom_gare_arrivee, 'gare_depart_id': gare_depart_id, 'gare_arrivee_id': gare_arrivee_id})

            return render(request, 'reservationhub/trajets.html', {'trajets': trajets_optimaux, 'gares': gares_disponibles, 'nom_gare_depart': nom_gare_depart, 'nom_gare_arrivee': nom_gare_arrivee, 'gare_depart_id': gare_depart_id, 'gare_arrivee_id': gare_arrivee_id})

    return render(request, 'reservationhub/trajets.html', {'trajets': trajets_disponibles, 'gares': gares_disponibles})



@login_required()
def mes_reservations(request):
    
    client = Client.objects.get(user=request.user)
    reservations = Reservation.objects.filter(utilisateur_reservation=client)
    return render(request, 'reservationhub/mes_reservations.html', {'reservations': reservations})



@login_required()
def edit_reservation(request, trajet_id):
    """
    Cette vue permet à un utilisateur authentifié de créer une nouvelle réservation pour un trajet spécifié.
    Si la méthode de la requête est POST et que le formulaire est valide, une nouvelle réservation est créée.
    Sinon, le formulaire est initialisé avec des données par défaut.

    Args:
        trajet_id (int): ID du trajet pour lequel la réservation est créée.

    Returns:
        HttpResponse: Retourne la page edit_reservation.html pour créer une nouvelle réservation.
    """
    
    # Initialisation :
    utilisateur = request.user
    client = Client.objects.get(user=utilisateur)  
    trajet = Trajet.objects.get(id=trajet_id)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)        # Créer le formulaire de réservation avec les données de la requête POST
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.trajet = trajet
            reservation.utilisateur_reservation = client  
            reservation.date_reservation = datetime.now()
            reservation.numero_place = random.randint(1, 200)
            reservation.numero_reservation = get_random_string(length=8, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            reservation.save()
            return redirect('reservationhub:mes_reservations')      # Rediriger l'utilisateur vers ses réservations
    else:
        passagers_disponibles = Passager.objects.filter(utilisateur=request.user)
        
        # Initialiser les données du formulaire avec des valeurs par défaut : 
        initial_data = {
            'date_reservation': datetime.now().date(),
            'numero_place': random.randint(1, 200),
            'numero_reservation': get_random_string(length=8, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
        }
        form = ReservationForm(initial=initial_data)
        form.fields['passager'].queryset = passagers_disponibles        # Limiter les passagers disponibles aux passagers associés à l'utilisateur
        
    return render(request, 'reservationhub/edit_reservation.html', {'form': form, 'trajet': trajet})


def creer_passager(request):
    """
    Cette vue permet à l'utilisateur de créer un nouveau passager.
    Si la méthode de la requête est POST et que le formulaire est valide, un nouveau passager est créé.
    Sinon, le formulaire est initialisé avec des champs vides.

    Returns:
        HttpResponse : Retourne la page creer_passage.html pour créer un nouveau passager.
    """
    
    utilisateur = request.user
    if request.method == 'POST':
        form = PassagerForm(request.POST)       # Créer le formulaire de passager avec les données de la requête POST
        if form.is_valid():
            passager = form.save(commit=False)
            passager.utilisateur = utilisateur  
            passager.save()
            return redirect('reservationhub:trajets')       # Rediriger l'utilisateur vers la page des trajets
    else:
        form = PassagerForm()       # Initialiser le formulaire avec des champs vides
    return render(request, 'reservationhub/creer_passager.html', {'form': form})

@login_required()
def modifier_reservation(request, reservation_id=None):
    """
    Cette vue permet à l'utilisateur authentifié de modifier une réservation existante.
    Si l'identifiant de la réservation est fourni, elle récupère cette réservation.
    Si l'utilisateur tente d'accéder à une réservation qui ne lui appartient pas, il est redirigé.
    Si la méthode de la requête est POST et que le formulaire est valide, la réservation est modifiée.
    Sinon, le formulaire est initialisé avec les données de la réservation existante.

    Args:
        reservation_id (int) : ID de la réservation à modifier.

    Returns:
        HttpResponse : Retourne la page modifier_reservation.html pour modifier la réservation.
    """
    
    # Initialisation :
    utilisateur = request.user
    client = Client.objects.get(user=utilisateur)  
    
    
    if (reservation_id == None):        # Vérifier si un identifiant de réservation est fourni
        reservation = None
    else:
        reservation = get_object_or_404(Reservation, id=reservation_id)
    
        if (reservation.utilisateur_reservation != client):     # Si l'user cherche à accéder à une réservation qui n'est pas la sienne
            return redirect('reservationhub:mes_reservations')

    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)      # Créer le formulaire de réservation avec les données de la requête POST et l'instance de la réservation
        if form.is_valid():
            form.save()
            return redirect('reservationhub:mes_reservations')
    else:
        passagers_disponibles = Passager.objects.filter(utilisateur=request.user)
        form = ReservationForm(instance=reservation)
        form.fields['passager'].queryset = passagers_disponibles        # Limiter les passagers disponibles aux passagers associés à l'utilisateur
        
    return render(request, 'reservationhub/modifier_reservation.html', {'form': form, 'reservation': reservation})


def register(request):
    """
    Cette vue permet à un utilisateur de s'inscrire.
    Si la méthode de la requête est POST et que le formulaire est valide, un nouvel utilisateur est créé et connecté.

    Returns:
        HttpResponse : Retourne la page register.html pour l'inscription.
    """
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)     # Créer le formulaire d'inscription avec les données de la requête POST
        if form.is_valid():
            user = form.save()      # Créer un nouvel utilisateur avec les données du formulaire
            login(request, user)        # Connecter l'utilisateur nouvellement créé
            return redirect('login')        # Rediriger l'utilisateur vers la page de connexion
    else:
        form = CustomUserCreationForm()
    return render(request, 'reservationhub/register.html', {'form': form})

def homepage(request):
    """
    Cette vue affiche la page d'accueil de l'application sans être connecté.
    Elle récupère tous les trajets et toutes les gares disponibles et les passe au template 'homepage.html'.

    Returns:
        HttpResponse : Retourne la page homepage.html avec les trajets et les gares disponibles.
    """
    
    trajets_disponibles = Trajet.objects.all()
    gares_disponibles = Gare.objects.all()
    return render(request, 'reservationhub/homepage.html', {'trajets': trajets_disponibles, 'gares': gares_disponibles})

@login_required()
def homepage_connecte(request):
    """
    Cette vue affiche la page d'accueil pour un utilisateur connecté.
    Elle récupère tous les trajets et toutes les gares disponibles et les passe au template 'homepage_connecte.html'.
    Si l'utilisateur n'est pas authentifié, il est redirigé vers la page de connexion.

    Returns:
        HttpResponse: Retourne la page homepage_connecte.html avec les trajets et les gares disponibles.
    """
    
    if request.user.is_authenticated:
        trajets_disponibles = Trajet.objects.all()
        gares_disponibles = Gare.objects.all()
        return render(request, 'reservationhub/homepage_connecte.html', {'trajets': trajets_disponibles, 'gares': gares_disponibles})
    
    # Si l'utilisateur n'est pas authentifié, rediriger vers la page de connexion :
    else:       
        return render(request, 'reservationhub/homepage_connecte.html', {})     

def get_charts_gare(request,gare_id):
    gare = Gare.objects.get(id=gare_id)
    reservations = Reservation.objects.filter(gare_depart=gare) | Reservation.objects.filter(gare_arrivee=gare)
    
    # Agréger les réservations par date
    reservations_par_date = reservations.annotate(date=TruncDate('date_reservation')).values('date').annotate(total=Count('id')).order_by('date')

    # Récupérer les dates et les nombres de réservations
    dates = [entry['date'] for entry in reservations_par_date]
    dates = sorted(dates)
    nombre_reservations = [entry['total'] for entry in reservations_par_date]

    # Formater les dates au format JavaScript Date (milliseconds since Unix epoch)
    dates_formattees = [int(datetime.combine(date, datetime.min.time()).timestamp()) * 1000 for date in dates].order_by('date')
        
    return JsonResponse({
        "title": f"Fréquentation gare {gare.nom}",
        "data": {
            "labels": dates_formattees,
            "datasets": [{
                "label": "Nombre de réservations",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "borderColor": "rgba(75, 192, 192, 1)",
                "data": nombre_reservations,
            }]
        },
    })
        
def get_charts_trajet(request, numero_trajet):
        trajet = Trajet.objects.get(id=numero_trajet)
        reservations = Reservation.objects.filter(trajet=trajet)
        
        dates = list(reservations.values_list('date_reservation', flat=True).distinct())
        dates = sorted(dates)
        nombre_reservations = [reservations.filter(date_reservation=date).count() for date in dates]
         
        return JsonResponse({
            "title": f"Réservations du trajet {numero_trajet}",
            "data": {
                "labels": dates,
                "datasets": [{
                    "label": "Amount ($)",
                    "backgroundColor": colorPrimary,
                    "borderColor": colorPrimary,
                    "data": nombre_reservations,
                }]
            },
        })


def trajets_chart_view(request, numero_trajet):
    return render(request, "reservationhub/admin_trajet_data.html", {'numero_trajet': numero_trajet})


def recherche_reservations(request):
    if request.user.is_superuser:
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
        if gare_name:
            context = {
                'gares_disponibles': gares_disponibles,
                'gare_name': gare_name,
                'selected': True,
                'selected_gare': gare_depart,
                'reservations_depart': reservations_depart,
                'reservations_arrivee': reservations_arrivee,
            }
        else:
            context = {
                'gares_disponibles': gares_disponibles,
                'gare_name': gare_name,
                'selected' : False,
                'reservations_depart': reservations_depart,
                'reservations_arrivee': reservations_arrivee,
            }
            
        return render(request, 'reservationhub/recherche_reservations.html', context)
    else:
        return render(request, 'registration/login.html', {})

def details_trajet_user(request, trajet_id):
    # Récupérer le trajet à partir de son ID
    trajet = get_object_or_404(Trajet, pk=trajet_id)
    depart=trajet.gare_depart
    arrivee=trajet.gare_arrivee
    
    # Passer le trajet et la liste des passagers au template pour l'affichage
    return render(request, 'reservationhub/details_trajet_user.html', {'trajet': trajet, 'trajet_id':trajet_id,'depart':depart,'arrivee':arrivee})

def details_trajet(request, trajet_id):
    # Récupérer le trajet à partir de son ID
    trajet = get_object_or_404(Trajet, pk=trajet_id)
    depart=trajet.gare_depart
    arrivee=trajet.gare_arrivee
    # Récupérer les passagers associés à ce trajet
    passagers = Passager.objects.filter(reservation__trajet=trajet)
    
    # Passer le trajet et la liste des passagers au template pour l'affichage
    return render(request, 'reservationhub/details_trajet.html', {'trajet': trajet, 'passagers': passagers,'trajet_id':trajet_id,'depart':depart,'arrivee':arrivee})

    