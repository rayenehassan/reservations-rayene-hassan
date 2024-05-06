import random

from faker import Faker
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reservations.settings")
import django
django.setup()

from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from reservationhub.models import Gare, Trajet, Passager, Client, Reservation

num_reservations = 500
num_passengers = 0

reservations = []
gares = Gare.objects.all()
passagers = Passager.objects.all()
clients = Client.objects.all()
trajets = Trajet.objects.all()
users = User.objects.all()

fake = Faker()

# Fonction pour générer des réservations aléatoires
def generate_reservations(num_reservations):

    for _ in range(num_reservations):
        # Sélection aléatoire d'une date et heure de départ et d'arrivée
        sign = random.choice([1, -1])
        date_reservation_random = datetime.now() + sign*timedelta(days=random.randint(1, 30))

        # Sélection aléatoire d'un passager et d'un client
        passager = random.choice(passagers)
        client = random.choice(clients)

        # Création de la réservation
        reservation = Reservation.objects.create(
            date_reservation=date_reservation_random,
            numero_reservation = get_random_string(length=8, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
            numero_place=random.randint(1, 100),
            passager=passager,
            trajet=random.choice(trajets),
            utilisateur_reservation=client
        )
        reservations.append(reservation)
        reservation.save()
    return reservations


def generate_passenger(num_passengers):
    passengers = []
    for _ in range(num_passengers):
        passenger = Passager.objects.create(
            nom = fake.first_name(),
            prenom =  fake.last_name(),
            date_naissance = fake.date_of_birth(minimum_age=20, maximum_age=80),
            utilisateur = random.choice(users)
        )
        passengers.append(passenger)
        passenger.save()
    return passengers


# Génération de 50 réservations
generated_reservations = generate_reservations(num_reservations)
generated_passengers = generate_passenger(num_passengers)
for passenger in generated_passengers:
    print(passenger)
